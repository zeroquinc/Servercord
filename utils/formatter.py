class Formatter:
    @staticmethod
    def indexer_value(release_indexer):
        indexer_words = release_indexer.split()
        indexer_value = "\n".join(indexer_words)
        return indexer_value
    
    @staticmethod
    def format_custom_formats(custom_format_score, custom_formats):
        return f"```Score: {custom_format_score}\nFormat: {', '.join(custom_formats)}```"