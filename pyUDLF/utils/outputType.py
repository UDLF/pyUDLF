from pyUDLF.utils import readData

# ler no config o metodo numerico ou str do rk


class OutputType:
    """
    Class to handle the outputs
    """

    def __init__(self, nome="None"):
        """
        Initial class parameters.
        """
        # dictionary with log data
        self.log_dict = dict()
        self.rk_path = nome
        self.matrix_path = nome
        self.log_path = nome

    def get_matrix(self):
        """
        Read matrix file

        Parameters:
            matrix_path -> matrix path

        Return:
            returns a matrix
        """
        if self.matrix_path is None:
            return None
        matrix = readData.read_matrix_file(self.matrix_path)
        return matrix

    def get_rks(self, top_k=1000):
        """
        Read string ou numeric ranked list

        Parameters:
            rk_patk -> ranked list path

        Return:
            returns a ranked list with image numbers or names
        """
        if self.rk_path is None:
            return None

        rks = readData.read_ranked_lists_file_string(self.rk_path, top_k=top_k)
        try:
            rks = [[int(elem) for elem in rk] for rk in rks]
        finally:
            return rks

    def get_log(self):
        """
        Returns the result of the execution !
        """
        self.log_dict = readData.read_log(self.log_path)
        # for param in self.log_dict:
        #    print("{} = {}".format(param, self.log_dict[param])) return ou nao?

        return self.log_dict
        # original n tinha nada

    def print_log(self, log_value=None):
        """
        Display log
        """
        if log_value is None:
            for param in self.log_dict:
                print("{:<10} = {}".format(param, self.log_dict[param]))
        else:
            if isinstance(log_value, dict):
                for param in log_value:
                    print("{:<10} = {}".format(param, log_value[param]))
