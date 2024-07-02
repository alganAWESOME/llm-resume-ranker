class RankString:
    """
    A bunch of useful functions for dealing with the rank-based
    naming convention of the files.
    """

    def string_from_rank(self, rank):
        rankstring = str(rank)
        len_string = 3

        return "0" * (len_string - len(rankstring)) + rankstring
    
    def decrement_rankstring(self, rankstring):
        rank = int(rankstring)
        rank -= 1
        return self.string_from_rank(rank)

    def increment_rankstring(self, rankstring):
        rank = int(rankstring)
        rank += 1
        return self.string_from_rank(rank)
    
    @staticmethod
    def extract_rankstring(filename):
        split = filename.split('-')
        return split[0], ''.join(split[1:])
    
    def derank_filename(self, filename):
        rankstring, og_filename = self.extract_rankstring(filename)
        rankstring = self.increment_rankstring(rankstring)

        return f'{rankstring}-{og_filename}'
    
    def add_rankstring_to_filename(self, filename, rank):
        return f'{self.string_from_rank(rank)}-{filename}'