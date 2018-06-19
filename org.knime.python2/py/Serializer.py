# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
#  Copyright by KNIME AG, Zurich, Switzerland
#  Website: http://www.knime.com; Email: contact@knime.com
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License, Version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses>.
#
#  Additional permission under GNU GPL version 3 section 7:
#
#  KNIME interoperates with ECLIPSE solely via ECLIPSE's plug-in APIs.
#  Hence, KNIME and ECLIPSE are both independent programs and are not
#  derived from each other. Should, however, the interpretation of the
#  GNU GPL Version 3 ("License") under any applicable laws result in
#  KNIME and ECLIPSE being a combined program, KNIME AG herewith grants
#  you the additional permission to use and propagate KNIME together with
#  ECLIPSE with only the license terms in place for ECLIPSE applying to
#  ECLIPSE and the GNU GPL Version 3 applying for KNIME, provided the
#  license terms of ECLIPSE themselves allow for the respective use and
#  propagation of ECLIPSE together with KNIME.
#
#  Additional permission relating to nodes for KNIME that extend the Node
#  Extension (and in particular that are based on subclasses of NodeModel,
#  NodeDialog, and NodeView) and that only interoperate with KNIME through
#  standard APIs ("Nodes"):
#  Nodes are deemed to be separate and independent programs and to not be
#  covered works.  Notwithstanding anything to the contrary in the
#  License, the License does not apply to Nodes, you are not required to
#  license Nodes under the License, and you are granted a license to
#  prepare and propagate Nodes, in each case even if such Nodes are
#  propagated with or for interoperation with KNIME.  The owner of a Node
#  may freely choose the license terms applicable to such Node, including
#  when such Node is propagated with or for interoperation with KNIME.
# ------------------------------------------------------------------------

"""
@author Clemens von Schwerin, KNIME GmbH, Konstanz, Germany
@author Patrick Winter, KNIME GmbH, Konstanz, Germany
@author Marcel Wiedenmann, KNIME GmbH, Konstanz, Germany
@author Christian Dietz, KNIME GmbH, Konstanz, Germany
"""

import numpy
from pandas import DataFrame

import debug_util
from DataTables import FromPandasTable
from DataTables import ToPandasTable
from PythonUtils import Simpletype
from PythonUtils import get_type_string
from PythonUtils import is_missing
from PythonUtils import types_are_equivalent


class Serializer(object):
    def __init__(self, serialization_library, type_extension_manager):
        self._serialization_library = serialization_library
        self._type_extension_manager = type_extension_manager

    def serialize_objects_to_bytes(self, data_frame, column_serializers):
        """
        Serialize all cells in the provided data frame to a bytes representation (inplace).
        @param data_frame a pandas.DataFrame containing columns to serialize
        @param column_serializers dict containing column names present in data_frame as keys and serializer_ids as
                                  values.
                                  A serializer_id should be the id of the java extension point on which the serializer
                                  is registered. Each column identified by the dict keys is serialized using the
                                  serializer provided by the TypeExtensionManager for the given serializer_id.
        """
        for column in column_serializers:
            serializer = self._type_extension_manager.get_serializer_by_id(column_serializers[column])
            col_idx = data_frame.columns.get_loc(column)
            if data_frame[column].dtype != 'object':
                data_frame[column] = data_frame[column].astype('object')
            for i in range(len(data_frame)):
                if debug_util.is_debug_enabled():
                    lastp = -1
                    if (i * 100 / len(data_frame)) % 5 == 0 and int(i * 100 / len(data_frame)) != lastp:
                        debug_util.debug_msg(str(i * 100 / len(data_frame)) + ' percent done (serialize)')
                        # lastp = int(i * 100/len(data_frame))
                # Using bracket acessor is necessary here for ensuring that there are
                # no unwanted type conversions
                value = data_frame[column][data_frame.index[i]]
                if value is not None:
                    if isinstance(value, list):
                        new_list = []
                        for inner_value in value:
                            if inner_value is None:
                                new_list.append(None)
                            else:
                                new_list.append(serializer.serialize(inner_value))
                        data_frame.iat[i, col_idx] = new_list
                    elif isinstance(value, set):
                        new_set = set()
                        for inner_value in value:
                            if inner_value is None:
                                new_set.add(None)
                            else:
                                new_set.add(serializer.serialize(inner_value))
                        data_frame.iat[i, col_idx] = new_set
                    else:
                        data_frame.iat[i, col_idx] = serializer.serialize(value)

    def deserialize_from_bytes(self, data_frame, column_serializers):
        """
        Deserialize all cells in the provided data frame from a bytes representation (inplace).
        @param data_frame a pandas.DataFrame containing columns to deserialize
        @param column_serializers dict containing column names present in data_frame as keys and deserializer_ids as
                                  values. A deserializer_id should be the id of the java extension point on which the
                                  deserializer is registered. Each column identified by the dict keys is deserialized
                                  using the deserializer provided by the TypeExtensionManager for the given
                                  deserializer_id.
        """

        # print('Data frame: ' + str(data_frame) + '\nserializers: ' + str(column_serializers) + '\n')
        for column in column_serializers:
            deserializer = self._type_extension_manager.get_deserializer_by_id(column_serializers[column])
            for i in range(len(data_frame)):
                if debug_util.is_debug_enabled():
                    lastp = -1
                    if (i * 100 / len(data_frame)) % 5 == 0 and int(i * 100 / len(data_frame)) != lastp:
                        debug_util.debug_msg(str(i * 100 / len(data_frame)) + ' percent done (deserialize)')
                        # lastp = int(i * 100/len(data_frame))
                col_idx = data_frame.columns.get_loc(column)
                # Using bracket accessor is necessary here for ensuring that there are no unwanted type conversions.
                value = data_frame[column][data_frame.index[i]]
                if isinstance(value, numpy.float64) and numpy.isnan(value):
                    value = None
                if value:
                    if isinstance(value, list):
                        new_list = []
                        for inner_value in value:
                            if isinstance(inner_value, numpy.float64) and numpy.isnan(inner_value):
                                inner_value = None
                            if inner_value:
                                new_list.append(deserializer.deserialize(inner_value))
                            else:
                                new_list.append(None)
                        data_frame.iat[i, col_idx] = new_list
                    elif isinstance(value, set):
                        new_set = set()
                        for inner_value in value:
                            if isinstance(inner_value, numpy.float64) and numpy.isnan(inner_value):
                                inner_value = None
                            if inner_value:
                                new_set.add(deserializer.deserialize(inner_value))
                            else:
                                new_set.add(None)
                        data_frame.iat[i, col_idx] = new_set
                    else:
                        data_frame.iat[i, col_idx] = deserializer.deserialize(value)
                else:
                    data_frame.iat[i, col_idx] = None

    def bytes_to_data_frame(self, data_bytes):
        """
        Converts data_bytes into a pandas DataFrame using the configured serialization library.
        For extension types appropriate deserializers are requested from the type extension manager.
        @param data_bytes a byte array containing a serialized KNIME table
        """
        column_names = self._serialization_library.column_names_from_bytes(data_bytes)
        if len(column_names) == 0:
            return DataFrame()
        column_types = self._serialization_library.column_types_from_bytes(data_bytes)
        column_serializers = self._serialization_library.column_serializers_from_bytes(data_bytes)
        table = ToPandasTable(column_names, column_types, column_serializers, self)
        self._serialization_library.bytes_into_table(table, data_bytes)
        return table.get_data_frame()

    def data_frame_to_bytes(self, data_frame, start_row_number=0):
        """
        Converts data_frame into a byte array using the configured serialization library.
        For extension types appropriate serializers are requested from the type extension manager.
        @param data_frame a pandas DataFrame containing the table to serializeregisterCommandHand
        @param start_row_number the corresponding row number to the first row of the dataframe.
                                Differs from 0 as soon as a table chunk is sent.
        """
        table = FromPandasTable(data_frame, self, start_row_number)
        # Uncomment to profile serialization time.
        # import cProfile
        # profilepath = os.path.join(os.path.expanduser('~'), 'profileres.txt')
        # prof = cProfile.Profile()
        # data_bytes = prof.runcall(_serializer.table_to_bytes, table)
        # prof.dump_stats(profilepath)
        data_bytes = self._serialization_library.table_to_bytes(table)
        return data_bytes

    def fill_flow_variables_from_data_frame(self, flow_variables, data_frame):
        """
        Fill the flow variable dict using a pandas DataFrame. The DataFrame is expected to contain only a single row.
        Each column name corresponds to a flow variable name and each cell to the respective flow variable's value.
        @param flow_variables  the flow variable dict to fill
        @param data_frame the pandas DataFrame to fill from
        """
        for column in data_frame.columns:
            simpletype = self.simpletype_for_column(data_frame, column)[0]
            if simpletype == Simpletype.INTEGER:
                flow_variables[column] = int(data_frame[column][0])
            elif simpletype == Simpletype.DOUBLE:
                flow_variables[column] = float(data_frame[column][0])
            else:
                flow_variables[column] = str(data_frame[column][0])

    @staticmethod
    def flow_variables_dict_to_data_frame(dictionary):
        """
        Convert a python dict to a pandas DataFrame in which each dict key represents a column and each dict value a
        cell in the respective column. Thus the resulting DataFrame will contain a single row.
        # @param dictionary a python dictionary
        """
        df = DataFrame()
        for key in dictionary:
            type_ = get_type_string(dictionary[key])
            if type_.find('int') >= 0 or type_.find('float') >= 0:
                df[key] = [dictionary[key]]
            else:
                df[key] = [str(dictionary[key])]
        return df

    def simpletype_for_column(self, data_frame, column_name):
        """
        Get the {@link Simpletype} of a column in the passed dataframe and the serializer_id if available (only
        interesting for extension types that are transferred as bytes).
        @param data_frame the dataframe containing the columns to evaluate
        @param column_name the name of the column in data_frame to evaluate
        @return tuple containing the {@link SimpleType} and the serializer_id (or None) of the column
        """

        column_serializer = None
        if len(data_frame.index) == 0:
            # if table is empty we don't know the types so we make them strings
            simple_type = Simpletype.STRING
        else:
            if data_frame[column_name].dtype == 'bool':
                simple_type = Simpletype.BOOLEAN
            elif data_frame[column_name].dtype == 'int32' or data_frame[column_name].dtype == 'int64':
                minvalue = data_frame[column_name][data_frame[column_name].idxmin()]
                maxvalue = data_frame[column_name][data_frame[column_name].idxmax()]
                int32min = -2147483648
                int32max = 2147483647
                if minvalue >= int32min and maxvalue <= int32max:
                    simple_type = Simpletype.INTEGER
                else:
                    simple_type = Simpletype.LONG
            elif data_frame[column_name].dtype == 'double' or self.column_type(data_frame, column_name) == float:
                simple_type = Simpletype.DOUBLE
            else:
                col_type = self.column_type(data_frame, column_name)
                if col_type is None:
                    # column with only missing values, make it string
                    simple_type = Simpletype.STRING
                elif types_are_equivalent(col_type, bool):
                    simple_type = Simpletype.BOOLEAN
                elif col_type is list or col_type is set:
                    is_set = col_type is set
                    list_col_type = self.list_column_type(data_frame, column_name)
                    if list_col_type is None:
                        # column with only missing values, make it string
                        if is_set:
                            simple_type = Simpletype.STRING_SET
                        else:
                            simple_type = Simpletype.STRING_LIST
                    elif types_are_equivalent(list_col_type, bool):
                        if is_set:
                            simple_type = Simpletype.BOOLEAN_SET
                        else:
                            simple_type = Simpletype.BOOLEAN_LIST
                    elif types_are_equivalent(list_col_type, int):
                        minvalue = 0
                        maxvalue = 0
                        for list_cell in data_frame[column_name]:
                            if list_cell is not None:
                                for cell in list_cell:
                                    if cell is not None:
                                        minvalue = min(minvalue, cell)
                                        maxvalue = max(maxvalue, cell)
                        int32min = -2147483648
                        int32max = 2147483647
                        if minvalue >= int32min and maxvalue <= int32max:
                            if is_set:
                                simple_type = Simpletype.INTEGER_SET
                            else:
                                simple_type = Simpletype.INTEGER_LIST
                        else:
                            if is_set:
                                simple_type = Simpletype.LONG_SET
                            else:
                                simple_type = Simpletype.LONG_LIST
                    elif types_are_equivalent(list_col_type, float):
                        if is_set:
                            simple_type = Simpletype.DOUBLE_SET
                        else:
                            simple_type = Simpletype.DOUBLE_LIST
                    elif types_are_equivalent(list_col_type, str):
                        if is_set:
                            simple_type = Simpletype.STRING_SET
                        else:
                            simple_type = Simpletype.STRING_LIST
                    else:
                        type_string = get_type_string(self.first_valid_list_object(data_frame, column_name))
                        column_serializer = self._type_extension_manager.get_serializer_id_by_type(type_string)
                        if column_serializer is None:
                            raise ValueError('Column ' + str(column_name) + ' has unsupported type ' + type_string)
                        if is_set:
                            simple_type = Simpletype.BYTES_SET
                        else:
                            simple_type = Simpletype.BYTES_LIST
                elif types_are_equivalent(col_type, str):
                    simple_type = Simpletype.STRING
                elif types_are_equivalent(col_type, bytes) or types_are_equivalent(col_type, bytearray):
                    # NOTE: raw bytestring requested here -> no serializer
                    simple_type = Simpletype.BYTES
                else:
                    type_string = get_type_string(self.first_valid_object(data_frame, column_name))
                    column_serializer = self._type_extension_manager.get_serializer_id_by_type(type_string)
                    if column_serializer is None:
                        raise ValueError('Column ' + str(column_name) + ' has columntype "'
                                         + str(data_frame[column_name].dtype)
                                         + '" although the first nonnull element has type "'
                                         + type_string + '". Mixed types in the column cannot be ruled out.'
                                         + ' You may convert the column type manually using the pandas.Series.astype'
                                           ' method.')
                    simple_type = Simpletype.BYTES
        return simple_type, column_serializer

    @staticmethod
    def column_type(data_frame, column_name):
        """
        Get the type of a column (fails if multiple types are found).
        """
        col_type = None
        for cell in data_frame[column_name]:
            if not is_missing(cell):
                if col_type is not None:
                    if not types_are_equivalent(type(cell), col_type):
                        raise ValueError('More than one type in column ' + str(column_name) + '. Found '
                                         + col_type.__name__ + ' and ' + type(cell).__name__)
                else:
                    col_type = type(cell)
        return col_type

    @staticmethod
    def list_column_type(data_frame, column_name):
        """
        Get the type of a list column (fails if multiple types are found).
        """
        col_type = None
        for list_cell in data_frame[column_name]:
            if list_cell is not None:
                for cell in list_cell:
                    if not is_missing(cell):
                        if col_type is not None:
                            if not types_are_equivalent(type(cell), col_type):
                                raise ValueError('More than one type in column ' + str(column_name) + '. Found '
                                                 + col_type.__name__ + ' and ' + type(cell).__name__)
                        else:
                            col_type = type(cell)
        if col_type == list or col_type == set:
            raise ValueError('Output table contains a nested collection. Nested collections are not supported, yet!')
        return col_type

    @staticmethod
    def first_valid_object(data_frame, column_name):
        """
        Returns the first object in a pandas DataFrame column that does not represent a missing type (None, NaN or NaT).
        """
        for cell in data_frame[column_name]:
            if not is_missing(cell):
                return cell
        return None

    @staticmethod
    def first_valid_list_object(data_frame, column_name):
        """
        Returns the first object contained in a list in a pandas DataFrame column that does not represent a missing type
        (None, NaN or NaT).
        """
        for list_cell in data_frame[column_name]:
            if list_cell is not None:
                for cell in list_cell:
                    if not is_missing(cell):
                        return cell
        return None