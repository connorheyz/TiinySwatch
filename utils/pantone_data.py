import json
import os
import math

class PantoneData:
    def __init__(self):
        self.names = []
        self.lab_values = []
        self._load_data()
        
    def _load_data(self):
        lab_json_path = os.path.join(os.path.dirname(__file__), 'pantone-lab-colors.json')
        with open(lab_json_path, 'r') as f:
            data = json.load(f)
            self.names = data['names']
            self.lab_values = data['lab_values']

    def get_lab(self, name):
        if name in self.names:
            index = self.names.index(name)
            return self.lab_values[index]
        return None
    
    def H_bar_prime(self, C1_prime, C2_prime, h1_prime, h2_prime):
        if C1_prime == 0 or C2_prime == 0:
            return h1_prime+h2_prime
        diff = abs(h1_prime - h2_prime)
        if (diff <= 180):
            return (h1_prime + h2_prime)/2.0
        elif (h1_prime + h2_prime < 360):
            return (h1_prime + h2_prime + 360)/2.0
        else:
            return (h1_prime + h2_prime - 360)/2.0
        
    def delta_h_prime(self, C1_prime, C2_prime, h1_prime, h2_prime):
        if C1_prime == 0 or C2_prime == 0:
            return 0
        diff = abs(h1_prime - h2_prime)
        if (diff <= 180):
            return h2_prime - h1_prime
        elif (h2_prime <= h1_prime):
            return h2_prime - h1_prime + 360
        else:
            return h2_prime - h1_prime - 360

    def a_prime(self, a, C_bar):
        return a + ((a/2.0) * (1 - math.sqrt((C_bar ** 7)/(C_bar**7 + 25.0**7))))
    
    def atan2_deg(self, y, x):
        return math.degrees(math.atan2(y, x)) % 360
    
    def get_delta_e_ab(self, L1, a1, b1, L2, a2, b2):
        return math.sqrt((L2-L1)**2 + (a2-a1)**2 + (b2-b1)**2)
    #l1, a1, b1 correspond to the reference color
    def get_distance(self, L1, a1, b1, L2, a2, b2):
        delta_L_prime = L2 - L1
        C1 = math.sqrt(a1**2 + b1**2)
        C2 = math.sqrt(a2**2 + b2**2)
        L_bar = (L1 + L2)/2.0
        C_bar = (C1+C2)/2.0
        a1_prime = self.a_prime(a1, C_bar)
        a2_prime = self.a_prime(a2, C_bar)
        C1_prime = math.sqrt(a1_prime**2 + b1**2)
        C2_prime = math.sqrt(a2_prime**2 + b2**2)
        delta_C_prime = C2_prime - C1_prime
        C_bar_prime = (C1_prime + C2_prime)/2.0
        h1_prime = self.atan2_deg(b1, a1_prime)
        h2_prime = self.atan2_deg(b2, a2_prime)
        delta_h_prime = self.delta_h_prime(C1_prime, C2_prime, h1_prime, h2_prime)
        delta_H_prime = 2.0 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(delta_h_prime/2.0))
        H_bar_prime = self.H_bar_prime(C1_prime, C2_prime, h1_prime, h2_prime)
        T = 1.0 - (0.17 * math.cos(math.radians(H_bar_prime - 30.0))) + (0.24 * math.cos(math.radians(2.0 * H_bar_prime))) + (0.32 * math.cos(math.radians(3.0*H_bar_prime + 6.0))) - (0.20 * math.cos(math.radians(4.0 * H_bar_prime - 63.0)))
        SL = 1.0 + ((0.015 * ((L_bar - 50)**2))/math.sqrt(20.0 + ((L_bar - 50.0)**2)))
        SC = 1.0 + 0.045 * C_bar_prime
        SH = 1.0 + 0.015 * C_bar_prime * T
        RT = -2.0 * math.sqrt((C_bar_prime ** 7)/(C_bar_prime**7 + 25.0**7)) * math.sin(math.radians(60.0 * math.exp(-(((H_bar_prime - 275)/25.0)**2))))
        delta_e_00 = (delta_L_prime/SL)**2 + (delta_C_prime/SC)**2 + (delta_H_prime/SH)**2 + (RT * (delta_C_prime/SC) * (delta_H_prime/SH))
        return math.sqrt(delta_e_00)

    def find_closest(self, target_l, target_a, target_b):
        # Find approximate position using L component
        closest_distance = float('inf')
        closest_name = None
        candidates = []
        
        for i in range(len(self.lab_values)):
            l, a, b = self.lab_values[i]
            distance = self.get_delta_e_ab(target_l, target_a, target_b, l, a, b) + self.get_distance(target_l, target_a, target_b, l, a, b)
            if distance < closest_distance:
                closest_distance = distance
                closest_name = self.names[i]
            if distance <= 5:
                candidates.append(i)

        return closest_name
   
    @staticmethod
    def generate_lab_json():
        from .color_utils import QColorEnhanced
        from PySide6.QtGui import QColor
        #Convert hex values to Lab and create optimized JSON structure.
        original_path = os.path.join(os.path.dirname(__file__), 'pantone-colors.json')
        output_path = os.path.join(os.path.dirname(__file__), 'pantone-lab-colors.json')

        with open(original_path, 'r') as f:
            data = json.load(f)
        
        colors = []
        for name, hex_value in zip(data['names'], data['values']):
            # Convert hex to Lab (D50 illuminant)
            srgb = QColorEnhanced(QColor(hex_value))
            
            lab = srgb.getLab()
            
            colors.append((name, [lab["L"], lab["a"], lab["b"]]))
        
        # Create sorted output structure
        output = {
            'names': [c[0] for c in colors],
            'lab_values': [c[1] for c in colors]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f)