#!/usr/bin/env python
import pandas as pd
import definitions

class SFCMonIBLTProcessor():

    def __init__(self):
        self.count_column = definitions.SFCMON_COUNT_REGISTER
        self.idx_columns = definitions.SFCMON_IDX_REGISTERS
        self.flow_columns = definitions.SFCMON_FLOW_REGISTERS
        self.metrics_columns = definitions.SFCMON_METRIC_REGISTERS

    def create_iblt(self, data):
        set_registers = set([self.count_column] + self.idx_columns + self.flow_columns + self.metrics_columns)
        set_datakeys = set(data.keys())
        diff = set_registers - set_datakeys
        if len(diff) > 0:
            return False,diff
        self.df = pd.DataFrame(data)
        return True,diff

    def listing(self):
        flows = []
        while True:
            searcheable_row = self.df[self.df[self.count_column] == 1].head(1)
            if not searcheable_row.empty:
                flow = {}
                selected_columns = self.idx_columns + self.flow_columns + self.metrics_columns
                for column in selected_columns:
                    flow[column] = searcheable_row.iloc[0][column]
                flows.append(flow)
                for idx_column in self.idx_columns:
                    idx_value = searcheable_row.iloc[0][idx_column]
                    self.remove(flow, idx_value)
            else:
                break
        columns = self.flow_columns + self.metrics_columns
        return pd.DataFrame(flows,columns=columns)

    def remove(self, flow, idx):
        self.df.iloc[idx][self.count_column] -= 1
        for column in self.idx_columns:
            self.df.iloc[idx][column] = self.df.iloc[idx][column] ^ flow[column]
        for column in self.flow_columns:
            self.df.iloc[idx][column] = self.df.iloc[idx][column] ^ flow[column]
        for column in self.metrics_columns:
            self.df.iloc[idx][column] -= flow[column]