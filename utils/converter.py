class Converter:
    @staticmethod
    def bytes_to_human_readable(size_in_bytes):
        if size_in_bytes < 1024 ** 3:  # Less than 1 GB
            result = size_in_bytes / (1024 ** 2)
            return "{:.2f}MB".format(result)
        else:  # 1 GB or greater
            result = size_in_bytes / (1024 ** 3)
            return "{:.2f}GB".format(result)