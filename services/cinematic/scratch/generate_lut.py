import os
import math

lut_path = "/home/junglee01/jarvis_universal/luts/thriller_teal_orange.cube"
os.makedirs(os.path.dirname(lut_path), exist_ok=True)

def apply_cinematic_grade(r, g, b):
    # 1. Compute luminance (standard ITU-R BT.601 weights)
    y = 0.299 * r + 0.587 * g + 0.114 * b
    
    # 2. S-curve for cinematic contrast enhancement
    def s_curve(x):
        return x * x * (3.0 - 2.0 * x)
        
    r_c = s_curve(r)
    g_c = s_curve(g)
    b_c = s_curve(b)
    
    # Recalculate luminance of contrast-adjusted color
    y_c = 0.299 * r_c + 0.587 * g_c + 0.114 * b_c
    
    # 3. Apply Teal shift in shadows (Luminance < 0.5)
    # Strength decreases as luminance increases
    shadow_weight = math.pow(max(0.0, 1.0 - y_c), 1.5)
    teal_target_r = 0.05 * y_c
    teal_target_g = 0.45 * y_c + 0.05
    teal_target_b = 0.55 * y_c + 0.10
    
    r_t = r_c + shadow_weight * 0.35 * (teal_target_r - r_c)
    g_t = g_c + shadow_weight * 0.20 * (teal_target_g - g_c)
    b_t = b_c + shadow_weight * 0.45 * (teal_target_b - b_c)
    
    # 4. Apply Orange shift in highlights and midtones
    # Strength increases as luminance increases
    highlight_weight = math.pow(y_c, 1.2)
    orange_target_r = 0.90 * y_c + 0.10
    orange_target_g = 0.55 * y_c + 0.05
    orange_target_b = 0.15 * y_c
    
    r_final = r_t + highlight_weight * 0.40 * (orange_target_r - r_t)
    g_final = g_t + highlight_weight * 0.25 * (orange_target_g - g_t)
    b_final = b_t + highlight_weight * 0.45 * (orange_target_b - b_t)
    
    # 5. Clip outputs to valid RGB range [0.0, 1.0]
    r_final = max(0.0, min(1.0, r_final))
    g_final = max(0.0, min(1.0, g_final))
    b_final = max(0.0, min(1.0, b_final))
    
    return r_final, g_final, b_final

with open(lut_path, "w") as f:
    f.write("LUT_3D_SIZE 33\n")
    # LUT .cube files standard iteration: R loops fastest, then G, then B
    for b_idx in range(33):
        b = b_idx / 32.0
        for g_idx in range(33):
            g = g_idx / 32.0
            for r_idx in range(33):
                r = r_idx / 32.0
                r_g, g_g, b_g = apply_cinematic_grade(r, g, b)
                f.write(f"{r_g:.6f} {g_g:.6f} {b_g:.6f}\n")

print(f"Generated stylized Teal and Orange thriller LUT at {lut_path}")
