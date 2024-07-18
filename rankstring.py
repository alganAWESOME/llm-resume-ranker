class RankString:
    """
    A bunch of useful functions for dealing with the rank-based
    naming convention of the files.
    """

    @staticmethod
    def string_from_rank(rank):
        rankstring = str(rank)
        len_string = 3

        return "0" * (len_string - len(rankstring)) + rankstring
    
    @staticmethod
    def rank_from_rankstring(rankstring):
        """You don't need to use this lul"""
        return int(rankstring)
    
    def decrement_rankstring(self, rankstring, by=1):
        rank = int(rankstring)
        rank -= by
        return self.string_from_rank(rank)

    def increment_rankstring(self, rankstring, by=1):
        rank = int(rankstring)
        rank += by
        return self.string_from_rank(rank)
    
    @staticmethod
    def get_rankstring(filename):
        """123-my_filename.png -> (123, my_filename.png)"""
        return filename[:3], filename[4:]
    
    def increment_ranked_filename(self, filename, by=1):
        rankstring, og_filename = self.get_rankstring(filename)
        rankstring = self.increment_rankstring(rankstring, by=by)

        return f'{rankstring}-{og_filename}'
    
    def decrement_ranked_filename(self, filename, by=1):
        return self.increment_ranked_filename(filename, by=-by)
    
    def add_rankstring_to_filename(self, filename, rank):
        return f'{self.string_from_rank(rank)}-{filename}'
    
    def rm_rankstring_from_filename(self, filename):
        """012-my_bad_cv.png -> my_bad_cv.png"""
        return self.get_rankstring(filename)[1]
    
    def is_rank_consecutive(self, filename1, filename2):
        """Return true if the ranks are consecutive and filename2 has bigger rank."""
        rankstring1,  _ = self.get_rankstring(filename1)
        rankstring2, _ = self.get_rankstring(filename2)
        return int(rankstring1) == int(rankstring2) - 1