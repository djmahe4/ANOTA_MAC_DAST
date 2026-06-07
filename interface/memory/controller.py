import json
import os

class MemoryController:
    """
    Manages the 4-tier memory consolidation pipeline for MAC-DAST agents.
    
    1. Working: Current LLM context window (handled by iii-engine/LangGraph).
    2. Episodic: Execution traces and state transitions (from BLM SQLite).
    3. Semantic: Knowledge graph of the codebase (from codebase-memory-mcp).
    4. Procedural: Reusable attack patterns and security rules (JSON/Vector).
    """
    def __init__(self, blm_db, codebase_client):
        self.blm_db = blm_db
        self.codebase = codebase_client

    def consolidate(self, decay_rate=None):
        """
        Background task to promote repeated Episodic patterns into Semantic memory.
        Also applies confidence decay to stale hypotheses.
        """
        from logic_engine.agent_config import AgentConfig
        decay_rate = decay_rate or AgentConfig.CONFIDENCE_DECAY
        
        # 1. Promote repeated transitions to Semantic knowledge
        self._promote_frequent_transitions()
        
        # 2. Apply exponential decay to confidence scores
        self._apply_confidence_decay(decay_rate)

    def _promote_frequent_transitions(self):
        """
        Identifies transitions observed multiple times across different traces
        and flags them as 'hardened' business logic rules.
        """
        cursor = self.blm_db.conn.cursor()
        # Find transitions observed across > 3 traces
        cursor.execute("""
            SELECT action_identifier, count(DISTINCT trace_id) as freq
            FROM transitions
            GROUP BY action_identifier
            HAVING freq >= 3
        """)
        frequent = cursor.fetchall()
        for action, freq in frequent:
            # Upsert into Semantic tier (using static_hints for now)
            self.blm_db.save_static_hint(
                "logic_rule", 
                action, 
                {"status": "hardened", "observation_count": freq}
            )

    def _apply_confidence_decay(self, decay_rate=0.9):
        """
        Decays confidence scores for observations and BLM edges over time.
        Confidence = Confidence * decay_rate for entries not accessed in the last 24h.
        """
        cursor = self.blm_db.conn.cursor()
        
        # Decay transitions not accessed in the last hour (for testing/demo purposes, 
        # real system would use 24h)
        cursor.execute("""
            UPDATE transitions 
            SET confidence_score = confidence_score * ? 
            WHERE last_accessed < datetime('now', '-1 hour')
        """, (decay_rate,))
        
        cursor.execute("""
            UPDATE observations 
            SET confidence_score = confidence_score * ? 
            WHERE last_accessed < datetime('now', '-1 hour')
        """, (decay_rate,))
        
        self.blm_db.conn.commit()

    def hybrid_search(self, query, k=None):
        """
        Performs Hybrid Search (BM25 + Vector) and unifies via Reciprocal Rank Fusion (RRF).
        """
        from logic_engine.agent_config import AgentConfig
        k = k or AgentConfig.RRF_K
        
        bm25_results = self._search_bm25(query)
        vector_results = self._search_vector(query)
        
        # RRF Algorithm: Score(d) = sum(1 / (k + rank(d)))
        scores = {}
        
        for rank, trace_id in enumerate(bm25_results, 1):
            scores[trace_id] = scores.get(trace_id, 0) + (1.0 / (k + rank))
            
        for rank, trace_id in enumerate(vector_results, 1):
            scores[trace_id] = scores.get(trace_id, 0) + (1.0 / (k + rank))
            
        # Sort by RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_ids

    def _search_bm25(self, query):
        """
        Full-text search using SQLite FTS5.
        """
        cursor = self.blm_db.conn.cursor()
        cursor.execute("""
            SELECT trace_id FROM observations_fts 
            WHERE content_summary MATCH ? 
            ORDER BY rank
        """, (query,))
        return [row[0] for row in cursor.fetchall()]

    def _search_vector(self, query):
        """
        Semantic search using Ollama embeddings and cosine similarity.
        """
        import numpy as np
        from logic_engine.agent_config import AgentConfig
        import struct
        
        # 1. Get query embedding
        query_vec = np.array(AgentConfig.get_embedding(query))
        
        # 2. Fetch all embeddings from DB
        cursor = self.blm_db.conn.cursor()
        cursor.execute("SELECT trace_id, embedding FROM vector_embeddings")
        rows = cursor.fetchall()
        
        results = []
        for trace_id, blob in rows:
            # Convert blob back to float array
            # Assuming float32, length depends on model (BGE-M3 is 1024)
            vec = np.frombuffer(blob, dtype=np.float32)
            
            # Compute cosine similarity
            similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
            results.append((trace_id, similarity))
            
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in results]

    def add_vector_index(self, trace_id, text):
        """
        Generates and stores an embedding for a trace's content.
        """
        import numpy as np
        from logic_engine.agent_config import AgentConfig
        
        embedding = AgentConfig.get_embedding(text)
        blob = np.array(embedding, dtype=np.float32).tobytes()
        
        cursor = self.blm_db.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO vector_embeddings (trace_id, embedding)
            VALUES (?, ?)
        """, (trace_id, blob))
        self.blm_db.conn.commit()

    def mark_accessed(self, trace_id):
        """
        Resets the decay curve for a specific trace.
        """
        cursor = self.blm_db.conn.cursor()
        cursor.execute("""
            UPDATE transitions SET last_accessed = CURRENT_TIMESTAMP WHERE trace_id = ?
        """, (trace_id,))
        cursor.execute("""
            UPDATE observations SET last_accessed = CURRENT_TIMESTAMP WHERE trace_id = ?
        """, (trace_id,))
        self.blm_db.conn.commit()

    def get_context_for_trace(self, trace_id):
        """
        Consolidates Episodic and Semantic memory for a specific execution trace.
        """
        # 1. Fetch Episodic Memory (What happened?)
        observation = self._get_observation(trace_id)
        
        # 2. Fetch Semantic Memory (What is the code structure?)
        # For each file in coverage, get structural hints and clean code
        files = observation.get("coverage_data", {}).keys()
        structural_context = []
        from logic_engine.agents.php_profiler import PHPProfiler
        php_prof = PHPProfiler()

        for file_path in files:
            hints = self.codebase.search_graph(name_pattern=f".*{file_path}.*")
            
            # If it's a PHP file, provide a cleaned snippet hint
            if file_path.endswith(".php"):
                # Use explicit root_path if available
                root = getattr(self.codebase, 'root_path', os.getcwd())
                full_path = os.path.abspath(os.path.join(root, file_path))
                
                if os.path.exists(full_path) and full_path.startswith(os.path.abspath(root)):
                    clean_code = php_prof.strip_noise(full_path)
                    hints.append({"type": "code_summary", "content": clean_code[:1000]}) # Limit size
            
            structural_context.append(hints)
            
        return {
            "episodic": observation,
            "semantic": structural_context
        }

    def _get_observation(self, trace_id):
        import json
        cursor = self.blm_db.conn.cursor()
        cursor.execute("SELECT * FROM observations WHERE trace_id = ?", (trace_id,))
        row = cursor.fetchone()
        if not row:
            return {}
            
        return {
            "trace_id": row[1],
            "timestamp": row[2],
            "source": row[3],
            "coverage_data": json.loads(row[4]),
            "state_data": json.loads(row[5]),
            "events_data": json.loads(row[6])
        }
