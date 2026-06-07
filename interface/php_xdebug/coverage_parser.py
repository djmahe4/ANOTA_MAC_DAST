class PHPXdebugParser:
    """
    Parses Xdebug coverage data and converts it into MAC-DAST telemetry format.
    """
    def parse_raw_data(self, raw_data):
        """
        Converts Xdebug array to unified JSON.
        Xdebug format: {filename: {line_no: status, ...}}
        Status: 1 = executed, -1 = not executed, -2 = no executable code
        """
        telemetry = {
            "type": "coverage",
            "coverage": {}
        }
        
        for filename, lines in raw_data.items():
            executed_lines = [
                int(line_no) for line_no, status in lines.items() 
                if status == 1
            ]
            executed_lines.sort()
            telemetry["coverage"][filename] = executed_lines
            
        return telemetry
