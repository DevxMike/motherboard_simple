import skfuzzy as fuzz
import numpy as np
from skfuzzy import control as ctrl

Z = ctrl.Antecedent(np.arange(0, 100, 0.002), 'Z')
THETA = ctrl.Antecedent(np.arange(-360, 360, 0.01), 'THETA')
LEFT = ctrl.Consequent(np.arange(-100, 100, 1), "LEFT")
RIGHT = ctrl.Consequent(np.arange(-100, 100, 1), "RIGHT")

Z['ZERO'] = fuzz.trapmf(Z.universe, [0, 0, 0, 0])
Z['S'] = fuzz.trimf(Z.universe, [0.003, 0.004, 0.004])
Z['B'] = fuzz.trapmf(Z.universe, [0.003, 0.04, 100.5, 200])

THETA['ZERO'] = fuzz.trimf(THETA.universe, [-8, 0, 8])
THETA['M'] = fuzz.trimf(THETA.universe, [-648, -360, -6])
THETA['P'] = fuzz.trimf(THETA.universe, [6, 360, 648])

LEFT['MM'] = fuzz.gaussmf(LEFT.universe, -100, 30)
RIGHT['MM'] = fuzz.gaussmf(RIGHT.universe, -100, 30)
LEFT['SM'] = fuzz.gaussmf(LEFT.universe, -50, 8.918)
RIGHT['SM'] = fuzz.gaussmf(RIGHT.universe, -50, 8.918)
LEFT['MP'] = fuzz.gaussmf(LEFT.universe, 100, 30)
RIGHT['MP'] = fuzz.gaussmf(RIGHT.universe, 100, 30)
LEFT['SP'] = fuzz.gaussmf(LEFT.universe, -50, 8.918)
RIGHT['SP'] = fuzz.gaussmf(RIGHT.universe, -50, 8.918)
LEFT['ZERO'] = fuzz.trapmf(LEFT.universe, [0, 0, 0, 0])
RIGHT['ZERO'] = fuzz.trapmf(RIGHT.universe, [0, 0, 0, 0])

rule1 = ctrl.Rule(Z['ZERO'] & THETA['ZERO'], (LEFT['ZERO'], RIGHT['ZERO']))
rule2 = ctrl.Rule(Z['ZERO'] & THETA['P'], (LEFT['ZERO'], RIGHT['ZERO']))
rule3 = ctrl.Rule(Z['ZERO'] & THETA['M'], (LEFT['ZERO'], RIGHT['ZERO']))

rule4 = ctrl.Rule(Z['S'] & THETA['ZERO'], (LEFT['SP'], RIGHT['SP']))
rule5 = ctrl.Rule(Z['S'] & THETA['M'], (LEFT['SP'], RIGHT['ZERO']))
rule6 = ctrl.Rule(Z['S'] & THETA['P'], (LEFT['ZERO'], RIGHT['SP']))

rule7 = ctrl.Rule(Z['B'] & THETA['ZERO'], (LEFT['MP'], RIGHT['MP']))
rule8 = ctrl.Rule(Z['B'] & THETA['M'], (LEFT['MP'], RIGHT['ZERO']))
rule9 = ctrl.Rule(Z['B'] & THETA['P'], (LEFT['ZERO'], RIGHT['MP']))

navi_ctrl = ctrl.ControlSystemSimulation(ctrl.ControlSystem([
    rule1, rule2, rule3, rule5, rule6, rule7, rule8, rule9
]))

def get_outputs(Z, THETA):
    global navi_ctrl

    navi_ctrl.input['Z'] = Z
    navi_ctrl.input['THETA'] = THETA

    navi_ctrl.compute()

    return (navi_ctrl.output['LEFT'], navi_ctrl.output['RIGHT'])


import GPS 

distance = GPS.distance()
azimuth = GPS.azimuth()

P1 = (40.741895, -73.989308)
PD = (40.732573, -73.962186)
PD2 = (40.722773, -74.087842)
PD3 = (40.81269061160269,-73.98693225545334)
imu = 0
Z = distance(P1, PD)
THETA = imu - azimuth(P1, PD)
print(f'distance:{Z}, theta:{THETA}')
print(get_outputs(Z, THETA))

Z = distance(P1, PD2)
THETA = imu - azimuth(P1, PD2)
print(f'distance:{Z}, theta:{THETA}')
print(get_outputs(Z, THETA))

Z = distance(P1, PD3)
THETA = imu - azimuth(P1, PD3)
print(f'distance:{Z}, theta:{THETA}')
print(get_outputs(Z, THETA))