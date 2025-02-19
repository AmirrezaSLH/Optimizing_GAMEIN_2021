import csv

import pyomo.environ as pyo


class ParametersReader:
    def __init__(self, csv_path, axis_0, axis_1):
        self.csv_path = csv_path
        self.axis_0 = axis_0
        self.axis_1 = axis_1

        self.axis_0_titles = []

    def read_csv(self):
        table = {}
        with open(self.csv_path) as f:
            reader = csv.reader(f, delimiter=",")
            line_cnt = 0

            for row in reader:
                assert len(row) == self.axis_1 + 1
                line_cnt += 1

                if line_cnt == 1:
                    self.axis_1_titles = [item.lower() for item in row[1:]]
                    continue

                table[row[0].lower()] = {self.axis_1_titles[i]: int(item) for i, item in enumerate(row[1:])}
                self.axis_0_titles.append(row[0].lower())

            assert line_cnt == self.axis_0 + 1

        return table

    def read_params(self):
        table = self.read_csv()

        print(table)
        # axis_0_set = set(self.axis_0_titles)
        axis_0_set = pyo.Set(initialize=self.axis_0_titles)
        # axis_1_set = set(self.axis_1_titles)
        axis_1_set = pyo.Set(initialize=self.axis_1_titles)

        param = pyo.Param(axis_0_set, axis_1_set, initialize=table)

        return axis_0_set, axis_1_set, param
