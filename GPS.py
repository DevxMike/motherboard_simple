import pynmea2
import numpy as np

class distance: 
    """Class provides __call__ method implementation which returns distance between two coords"""
    def __deg_to_rad(self, coords1 : tuple, coords2 : tuple) -> list:
        """
        Returns two tuples with coords represented in radians\n
        coords1 : (latitude1, longitude1)\n
        coords2 : (latitude2, longitude2)\n
        """
        return [
            (np.deg2rad(coords1[0]), np.deg2rad(coords1[1])), 
            (np.deg2rad(coords2[0]), np.deg2rad(coords2[1]))
        ]

    def __call__(self, coords1 : tuple, coords2 : tuple) -> float:
        """
        Returns distance in km\n
        coords1 : (latitude1, longitude1)\n
        coords2 : (latitude2, longitude2)\n
        """
        # convert degrees to radians
        [lat1, lon1], [lat2, lon2] = self.__deg_to_rad(coords1, coords2)

        dlon = lon2 - lon1 # get longtitude diff
        dlat = lat2 - lat1 # get latitude diff

        s = np.sin      # get pointers to functions so shorter names can be used
        c = np.cos
        at = np.arctan2

        a = (s(dlat/2) ** 2 + c(lat1)*c(lat2)*(s(dlon/2) ** 2)) # get angle
        angle = 2 * at(np.sqrt(a), np.sqrt(1 - a))
        
        return  angle * 6371.0 # return distance in km

class azimuth: 
    """Class provides __call__ method implementation which returns distance between two coords"""
    def __deg_to_rad(self, coords1 : tuple, coords2 : tuple) -> list:
        """
        Returns two tuples with coords represented in radians\n
        coords1 : (latitude1, longitude1)\n
        coords2 : (latitude2, longitude2)\n
        """
        return [
            (np.deg2rad(coords1[0]), np.deg2rad(coords1[1])), 
            (np.deg2rad(coords2[0]), np.deg2rad(coords2[1]))
        ]

    def __call__(self, coords1 : tuple, coords2 : tuple) -> float:
        """
        Returns distance in km\n
        coords1 : (latitude1, longitude1)\n
        coords2 : (latitude2, longitude2)\n
        """
        # convert degrees to radians
        [lat1, lon1], [lat2, lon2] = self.__deg_to_rad(coords1, coords2)

        dlon = lon2 - lon1 # get longtitude diff

        s = np.sin      # get pointers to functions so shorter names can be used
        c = np.cos
        at = np.arctan2

        angle = at(s(dlon) * c(lat2), c(lat1)*s(lat2) - s(lat1)*c(lat2)*c(dlon))

        return np.rad2deg(angle)