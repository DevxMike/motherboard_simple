import serial
import serial.tools.list_ports
import time
from base64 import decode

class LIDAR:
    __commands = {
        "version" : b"\x56\x0A",
        "laser_on" : b"\x4C\x31\x0A",
        "laser_off" : b"\x4C\x30\x0A"
    }
    def __decode_bytes(self, bytes_list):
        result = []
        for byte_tuple in bytes_list:
            [byte1, byte2] = byte_tuple
            byte1 = byte1 - 0x30
            byte2 = byte2 - 0x30
            byte1 = byte1 << 6
            result.append(byte1 | byte2)
        return result

    def __get_distances_from_raw_data(self, raw_data):
        result = []
        for row in raw_data:
            for i in range (0, len(row), 2):
                result.append((ord(row[i]), ord(row[i+1])))

        return result
        
    def scan_area(self, starting_point, ending_point, cluster_count):
        cmd = bytes(f"G{starting_point}{ending_point}{cluster_count}\n", "ascii")

        self.__connection.write(cmd)
        time.sleep(0.1)
        response = self.__connection.read_all().decode("ascii")
        response = response.split("\n")

        if(response[1] != '0'):
            Exception("Error")
        else:
            response = response[2:-2]

        return self.__decode_bytes(self.__get_distances_from_raw_data(response))

    def get_lidar_version(self):
        self.__connection.write(self.__commands["version"])
        time.sleep(0.1)
        response = self.__connection.read_all()
        return response

    def switch_laser(self, on_off):
        self.__connection.write(self.__commands["laser_on" if on_off else "laser_off"])
        time.sleep(0.1)
        response = self.__connection.read_all()

        return response

    def __get_connection_to_lidar(self, verbose):
        const_hwid = "15D1:0000"
        connected = False
        retries = 0
        connection = None

        while connected == False:
            ports = serial.tools.list_ports.comports()
            port = None
            for dev, desc, hwid in sorted(ports):
                    if(const_hwid in hwid):
                        port = dev
                        try:
                            connection = serial.Serial(port=port, baudrate=19200) 
                            connected = True
                            if(verbose):
                                msg = "retry" if retries == 1  else "retries"
                                print(f"Lidar connected after {retries} {msg}")
                            return connection
                        except:        
                            retries += 1
    
    def __init__(self):
        self.__connection = self.__get_connection_to_lidar(True)

lidar = LIDAR()
print(lidar.scan_area("044", "725", "01"))
