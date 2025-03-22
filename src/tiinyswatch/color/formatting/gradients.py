from tiinyswatch.color import QColorEnhanced

class GradientFormatters:
    @staticmethod
    def css_gradient_string(colors, continuous=True):
        if not colors:
            return ""
        n = len(colors)
        if continuous:
            stops = []
            if n == 1:
                stops = [f"{colors[0].name()} 0%", f"{colors[0].name()} 100%"]
            else:
                for i, col in enumerate(colors):
                    fraction = i / (n - 1) * 100
                    stops.append(f"{col.name()} {fraction:.0f}%")
            return "linear-gradient(to right, " + ", ".join(stops) + ")"
        else:
            stops = []
            step = 100 / n
            for i, col in enumerate(colors):
                start = i * step
                end = (i + 1) * step
                stops.append(f"{col.name()} {start:.0f}% {end:.0f}%")
            return "linear-gradient(to right, " + ", ".join(stops) + ")"

    @staticmethod
    def qlinear_gradient_string(colors):
        if not colors:
            return ""
        n = len(colors)
        stops = []
        if n == 1:
            stops = [f"stop:0 {colors[0].name()}", f"stop:1 {colors[0].name()}"]
        else:
            for i, col in enumerate(colors):
                fraction = i / (n - 1)
                stops.append(f"stop:{fraction:.2f} {col.name()}")
        return "qlineargradient(x1:0, y1:0, x2:1, y2:0, " + ", ".join(stops) + ")"