import json
import re
import time

from pros.gui_data.db.sqlite_wrapper import SQLiteWrapper

DATA_HEADER = "GUI_DATA_8378"
CONFIG_HEADER = "GUI_DATA_CONF_8378"
CONFIG_END_HEADER = "GUI_DATA_CONF_3434_END"


class ChartManager:
    class Status:
        STOPPED = 0
        AWAITING_CONFIGURATION = 1
        RECEIVING_DATA = 2

    def __init__(self):
        self.status = self.Status.AWAITING_CONFIGURATION
        self.config_string = ""
        self.config_json = None
        self.db = None
        self.table = None

        return

    def connect(self):
        return

    def parse(self, raw_data_string):
        try:
            header, data = self.__parse_data(raw_data_string)

            if self.status == self.Status.AWAITING_CONFIGURATION:
                if data.strip().endswith(CONFIG_END_HEADER):
                    self.config_string += data[0:-(len(CONFIG_END_HEADER)+1)]

                    print(self.config_string)

                    self.config_json = json.loads(self.config_string)

                    columns = {}

                    for chart in self.config_json:
                        columns[chart] = "REAL"

                    self.db = SQLiteWrapper("guidata")
                    self.db.open()


                    self.db.begin()
                    self.table = self.db.create_table("data", date="timestamp", **columns)
                    self.db.commit()

                    print("Setting status")
                    self.status = self.Status.RECEIVING_DATA
                    return
                else:
                    self.config_string += re.sub('\n', '', self.config_string)
                    return
            elif self.status == self.Status.RECEIVING_DATA:
                print("HEADER: " + header.strip())
                if header.strip() == DATA_HEADER:
                    data_json = json.loads(data)

                    # I'm going to assume this will still be in order
                    data_values = []

                    for key, value in data_json.items():
                        data_values.append(value)

                    self.db.begin()
                    self.table.insert_row(time.time(), *data_values)
                    self.db.commit()
                    return
        except TypeError:
            return

    def __parse_data(self, raw_data_string):
        print(raw_data_string)

        split = raw_data_string.split("|")

        print(split)

        # We need to have at least 2 elements when splitting off of '|'
        if len(split) != 2:
            print("Split length not 2")
            return None

        # Split into header and data components
        header = split[0]  # Contains the file header
        data = split[1]  # Contains the JSON data

        return header, data
