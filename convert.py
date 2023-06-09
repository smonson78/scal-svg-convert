import sys
import re
from xml.sax import parse
from xml.sax.handler import ContentHandler

import math

debug = False

# Rotate a point around an origin point by an angle
def rotate(origin, point, angle):
    dx = point[0] - origin[0]
    dy = point[1] - origin[1]
    dx_ = (dx * math.cos(angle)) - (dy * math.sin(angle))
    dy_ = (dx * math.sin(angle)) + (dy * math.cos(angle))
    return (origin[0] + dx_, origin[1] + dy_)

# Scale a 1-dimensional quantity
def scale(origin, point, factor):
    d = point - origin
    d_ = d * factor
    return origin + d_

# p1 and p2 are two points on the ellipse
# sweep is 0 for anti-clockwise, 1 for clockwise
def centralise_ellipse(p1, p2, sweep):
    pass

def elliptical_arc_to_bezier(x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
    pass

def as_degrees(r):
    return r / math.pi * 180.0

number_re = re.compile('\s*([+-]?[0-9.]+e[+-]?[0-9]+|-?[0-9]*\.[0-9]+|-?[0-9]+),?')
cmd_re = re.compile('\s*([MLHVCSQTAZ])', re.IGNORECASE)

def parse_num(n):
    n = n.strip()
    if n == "":
        return None
    return float(n)

def optional_p(arg):
    if arg == None:
        return ''
    if arg == int(arg):
        return str(int(arg))
    return str(arg)

def fix_path(path):
    commands = []
    this_cmd = None
    last_pos = (0, 0)

    # The point to return to when the current subpath is closed
    initial_point = None

    def set_last_pos(x, y):
        nonlocal last_pos, initial_point
        last_pos = (x, y)

        # If this is the first move in the path, set initial_point as well
        if initial_point == None:
            initial_point = (x, y)
            #print(f"<!-- New start point: {initial_point} -->")

    def set_last_pos_relative(x, y):
        nonlocal last_pos, initial_point
        last_pos = (last_pos[0] + x, last_pos[1] + y)

        # If this is the first move in the path, set initial_point as well
        if initial_point == None:
            initial_point = last_pos
            #print(f"<!-- New start point (relative???): {initial_point} -->")

    path = path.strip()
    while path != "":
        
        match = cmd_re.match(path)
        if match:
            if this_cmd:
                commands.append(this_cmd)
            this_cmd = [match.group(1)]
        else:
            match = number_re.match(path)
            if match:
                this_cmd.append(parse_num(match.group(1)))
            else:
                print("Error in path:")
                print(path)
                sys.exit(1)
        
        path = path[match.end():]

    if this_cmd:
        commands.append(this_cmd)

    # Interpret commands
    first_command = True
    last_command_was_z = False
    new_commands = []
    for c in commands:
        cmd = c[0].lower()
        args = c[1:]
        isrelative = c[0].islower()
        #print(f"<!-- Next command is {c[0]} - current point is {last_pos}, start point is {initial_point} -->")

        if cmd == "z":
            # Close current path. 
            last_pos = initial_point
            last_command_was_z = True

        if cmd == "h":
            # Horizontal line: 1 parameter (horizontal position)
            while len(args) >= 1: 
                if isrelative:
                    set_last_pos_relative(args[0], 0)
                else:
                    set_last_pos(args[0], last_pos[1])
                args = args[1:]

        if cmd == "v":
            # Vertical line: 1 parameter (vertical position)
            while len(args) >= 1: 
                if isrelative:
                    set_last_pos_relative(0, args[0])
                else:
                    set_last_pos(last_pos[0], args[0])
                args = args[1:]

        if cmd == "m":
            # Move: 2 parameters, with special handling for the first command in the path
            while len(args) >= 2:
                if first_command:
                    # Treat as absolute
                    set_last_pos(args[0], args[1])
                elif isrelative:
                    set_last_pos_relative(args[0], args[1])
                else:
                    set_last_pos(args[0], args[1])

                # Set a new initial point
                initial_point = last_pos

                args = args[2:]

        if cmd in ["l", "t"]:
            # Move to, Line, Smooth quadratic bezier: 2 parameters, with final position in 0 and 1

            while len(args) >= 2: 
                if isrelative:
                    set_last_pos_relative(args[0], args[1])
                else:
                    set_last_pos(args[0], args[1])
                args = args[2:]

        if cmd == "c":
            # Bezier curve: 6 parameters, with final position in 4 and 5
            while len(args) >= 6: 
                if isrelative:
                    set_last_pos_relative(args[4], args[5])
                else:
                    set_last_pos(args[4], args[5])
                args = args[6:]

        if cmd in ["s", "q"]:
            # Smooth bezier, Quadratic bezier: 4 parameters, with final position in 2 and 3
            while len(args) >= 4: 
                if isrelative:
                    set_last_pos_relative(args[2], args[3])
                else:
                    set_last_pos(args[2], args[3])
                args = args[4:]

        if cmd == "a":
            #print("<!-- ======================================= -->")
            arcs = args[:]
            beziers = []
            while len(arcs) >= 7:
                arc = arcs[:7]
                arcs = arcs[7:]

                if isrelative:
                    end_pos = (last_pos[0] + arc[5], last_pos[1] + arc[6])
                    #print(f"<!-- Relative arc from {last_pos} to {last_pos} + {(arc[5], arc[6])} = {end_pos} -->")
                else:
                    end_pos = (arc[5], arc[6])
                    #print(f"<!-- Absolute arc from {last_pos} to {end_pos} -->")

                rx = arc[0]
                ry = arc[1]
                #print(f"<!-- ellipse radii are x={rx}, y={ry} -->")

                angle = (arc[2] / 180) * math.pi
                large_arc_flag = int(arc[3])
                sweep_flag = int(arc[4])

                # Which side the circle's centre point will be on
                side = bool(large_arc_flag) ^ bool(sweep_flag)

                # Eliminate "angle" variable by rotating everything (which is just the end point) around the start point.
                # Now r1 and r2 should line up with x and y axes
                rotated_end_point = rotate(last_pos, end_pos, -angle)
                
                # Scale the ellipse to r1 = 1, r2 = 1 (circle)
                # starting point (last_pos) remains at the same coords, but end_point will now be scaled_end_point.
                rx_scale = 1.0 / rx
                ry_scale = 1.0 / ry

                scaled_end_point_x = scale(last_pos[0], rotated_end_point[0], rx_scale)
                scaled_end_point_y = scale(last_pos[1], rotated_end_point[1], ry_scale)
                scaled_end_point = (scaled_end_point_x, scaled_end_point_y)

                p1 = last_pos
                x1 = p1[0]
                y1 = p1[1]

                p2 = scaled_end_point
                x2 = p2[0]
                y2 = p2[1]

                # Distance between start and end points of the arc:
                q = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))
                #print(f"<!-- q = {q} and half q is {q/2} -->")

                #print(f"<!-- Distance between p1 and p2 is {q} -->")
                # Linear midpoint on line p1,p2
                x3 = (x1 + x2) / 2
                y3 = (y1 + y2) / 2
                #print(f"<!-- midpoint: {p1} {p2} {(x3, y3)} -->")

                # Axis distances between endpoints and middle
                xa = x3 - x1
                ya = y3 - y1
                #print(f"<!-- xa={xa}, ya={ya} -->")

                # We'll call half q "a" and the other diagonal "b"
                a = q / 2
                #print(f"<!-- a={a} -->")

                # Hypotenuse of the triangle with "b" on it is circle radius, therefore 1 squared = 1.
                b = math.sqrt(1 - math.pow(a, 2))
                #print(f"<!-- b={b} -->")

                # Find circle centre
                if side == False:
                    #midpoint_x = x3 - math.sqrt(1 - math.pow(q / 2, 2)) * (y1 - y2) / q
                    #midpoint_y = y3 - math.sqrt(1 - math.pow(q / 2, 2)) * (x2 - x1) / q
                    midpoint_x = x3 + (b * ya / a)
                    midpoint_y = y3 - (b * xa / a)
                else:
                    # crash here due to sqrt of negative number:
                    #midpoint_x = x3 + math.sqrt(1 - math.pow(q / 2, 2)) * (y1 - y2) / q
                    #midpoint_y = y3 + math.sqrt(1 - math.pow(q / 2, 2)) * (x2 - x1) / q
                    midpoint_x = x3 - (b * ya / a)
                    midpoint_y = y3 + (b * xa / a)
                #print(f"<!-- Circle midpoint is {(midpoint_x, midpoint_y)} -->")
                #print(f"<!-- Scaled midpoint is {(scale(x1, midpoint_x, rx), scale(y1, midpoint_y, ry))} -->")

                if debug:
                    # Arc circle, drawn 120 below ellipse - sized for rx (so it's round))
                    # Everything is scaled for rx, including y axis
                    print(f'<circle style="fill:#00ff00;fill-opacity:0.5" r="{rx}" cx="{scale(x1, midpoint_x, rx)}" cy="{scale(y1, midpoint_y, rx) + 120}" />')
                    # Start and end points on the circle's perimeter (start is red)
                    print(f'<circle style="fill:#ff0000;fill-opacity:1" r="2" cx="{x1}" cy="{y1 + 120}" />')
                    print(f'<circle style="fill:#000000;fill-opacity:1" r="2" cx="{scale(x1, x2, rx)}" cy="{scale(y1, y2, rx) + 120}" />')
                    # Construction lines
                    print(f'<path style="stroke:#000000;stroke-width:0.25;fill-opacity:0" d="M {x1} {y1 + 120} L {scale(x1, midpoint_x, rx)} {scale(y1, midpoint_y, rx) + 120}" />')
                    print(f'<path style="stroke:#000000;stroke-width:0.25;fill-opacity:0" d="M {scale(x1, x2, rx)} {scale(y1, y2, rx) + 120} L {scale(x1, midpoint_x, rx)} {scale(y1, midpoint_y, rx) + 120}" />')

                # point 1 relative to origin
                rel_x1 = x1 - midpoint_x
                rel_y1 = y1 - midpoint_y
                #print(f"<!-- point 1 original coords: {p1} -->")
                #print(f"<!-- point 1 relative coords: {rel_x1:.4f}, {rel_y1:.4f} -->")
                #p1_angle = math.asin(rel_y1) if side else (math.pi + math.asin(rel_y1))
                # Y is negative because SVG's coords are upside down compared to python's math module's
                p1_angle = math.atan2(-rel_y1, rel_x1) % (2 * math.pi)
                #print(f"<!-- point 1 angle: {as_degrees(p1_angle):.4f} -->")

                # point 2 relative to origin
                rel_x2 = x2 - midpoint_x
                rel_y2 = y2 - midpoint_y
                #print(f"<!-- point 2 original coords: {p2} -->")
                #print(f"<!-- point 2 relative coords: {rel_x2:.4f}, {rel_y2:.4f} -->")
                #p2_angle = math.asin(rel_y2) if side else (math.pi + math.asin(rel_y2))
                p2_angle = math.atan2(-rel_y2, rel_x2) % (2 * math.pi)
                #print(f"<!-- point 2 angle: {as_degrees(p2_angle):.4f} -->")

                # Divide the arc up into 90-degree segments
                segments = []
                segment_start_angle = p1_angle

                if sweep_flag:
                    angle_remain = (p1_angle if p1_angle > p2_angle else ((2 * math.pi) + p1_angle)) - p2_angle
                else:
                    angle_remain = (p2_angle if p2_angle > p1_angle else ((2 * math.pi) + p2_angle)) - p1_angle

                #print(f"<!-- total angle: {as_degrees(angle_remain)} -->")
                while angle_remain > 0:
                    seg_angle = min(angle_remain, math.pi / 2)
                    segment_end_angle = segment_start_angle - seg_angle if sweep_flag else segment_start_angle + seg_angle

                    #print(f"<!--     segment with angle {as_degrees(seg_angle)} -->")
                    #print(f"<!--         start angle {as_degrees(segment_start_angle)} to {as_degrees(segment_end_angle)}-->")

                    # Start angle, end angle
                    segments.append((segment_start_angle, segment_end_angle))

                    # Ready for next segment
                    segment_start_angle = segment_end_angle
                    angle_remain -= seg_angle

                # Generate cubic beziers for the segments
                #print(f"<!-- Generating {len(segments)} cubic beziers: -->")

                for start_angle, end_angle in segments:
                    #print(f"<!--     From {as_degrees(start_angle)} to {as_degrees(end_angle)}: -->")

                    # Start point of control handle 1 line is on circumference of circle at start of arc
                    # Tangent of control handle 1 line is tangent of circle angle
                    sp_x = math.cos(start_angle)
                    sp_y = -math.sin(start_angle)
                    #print(f"<!--         Start point of segment is {(sp_x, sp_y)} -->")

                    # Start point of control handle 2 line is on circumference of circle at end of arc
                    # Tangent of control handle 2 line is tangent of circle angle
                    ep_x = math.cos(end_angle)
                    ep_y = -math.sin(end_angle)
                    #print(f"<!--         End point of segment is {(ep_x, ep_y)} -->")

                    # Find midpoint of arc (on circle)
                    if sweep_flag:
                        # Clockwise, i.e. going negative. Start angle should be higher.
                        eff_start_angle = start_angle if start_angle > end_angle else (start_angle + (2 * math.pi))
                        half_angle = (eff_start_angle - end_angle) / 2
                        midpoint_angle = start_angle - half_angle
                    else:
                        # Anti-clockwise, going positive. Start angle should be lower.
                        eff_start_angle = start_angle if start_angle < end_angle else (start_angle - (2 * math.pi))
                        half_angle = (end_angle - eff_start_angle) / 2
                        midpoint_angle = start_angle + half_angle

                    #print(f"<!--         sweep={sweep_flag} eff_start_angle={as_degrees(eff_start_angle)} half_angle={as_degrees(half_angle)} midpoint_angle={as_degrees(midpoint_angle)} -->")

                    # Find tangent line of midpoint
                    #print(f"<!--         Slope of line from midpoint is 1:{math.tan(midpoint_angle + (math.pi / 2))} -->")
                    
                    # I'm running out of variable names
                    fig_a = half_angle
                    fig_y = math.cos(fig_a)
                    #fig_4x = (1.0 - fig_y) * 4 / 3
                    #print(f"<!--         y={fig_y} and 4x={fig_4x} -->")

                    #fig_2L = fig_4x / math.cos(fig_a)
                    fig_2L = 4.0 / 3.0 * math.tan(half_angle / 2)

                    #print(f"<!--         Got L value of {fig_2L / 2} -->")
                    #print(f"<!--           a={as_degrees(half_angle)} -->")
                    #print(f"<!--           tan(a/2)={math.tan(half_angle/2)} -->")
                    #print(f"<!--           r={1} -->")
                    #print(f"<!--           L={fig_2L/2} -->")

                    # start and end control points, at right angles to start and end points at a distance of 2L
                    adjustment = -(math.pi / 2) if sweep_flag else (math.pi / 2)

                    start_2L_x = midpoint_x + sp_x + (math.cos(start_angle + adjustment) * fig_2L)
                    start_2L_y = midpoint_y + sp_y + (-math.sin(start_angle + adjustment) * fig_2L)

                    end_2L_x = midpoint_x + ep_x + (math.cos(end_angle - adjustment) * fig_2L)
                    end_2L_y = midpoint_y + ep_y + (-math.sin(end_angle - adjustment) * fig_2L)

                    # Scale back up to original size
                    us_scontrol_x = scale(x1, start_2L_x, rx)
                    us_scontrol_y = scale(y1, start_2L_y, ry)
                    us_econtrol_x = scale(x1, end_2L_x, rx)
                    us_econtrol_y = scale(y1, end_2L_y, ry)
                    us_seg_endpoint = (scale(x1, midpoint_x + ep_x, rx), scale(y1, midpoint_y + ep_y, ry))

                    # Rotate control points back to original angle
                    r_scontrol = rotate(last_pos, (us_scontrol_x, us_scontrol_y), angle)
                    r_econtrol = rotate(last_pos, (us_econtrol_x, us_econtrol_y), angle)

                    # Rotated end point for segment
                    r_seg_end = rotate(last_pos, us_seg_endpoint, angle)

                    beziers.append([r_scontrol[0], r_scontrol[1], r_econtrol[0], r_econtrol[1], 
                        r_seg_end[0], r_seg_end[1]])

                    if debug:
                        # Construction lines
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="1" cx="{scale(x1, midpoint_x + sp_x, rx)}" cy="{scale(y1, midpoint_y + sp_y, rx) + 120}" />')
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="1" cx="{scale(x1, midpoint_x + ep_x, rx)}" cy="{scale(y1, midpoint_y + ep_y, rx) + 120}" />')
                        print(f'<path style="stroke:#000000;stroke-width:0.25;fill-opacity:0" d="M {scale(x1, midpoint_x + sp_x, rx)} {scale(y1, midpoint_y + sp_y, rx) + 120} L {scale(x1, midpoint_x, rx)} {scale(y1, midpoint_y, rx) + 120}" />')
                        print(f'<path style="stroke:#000000;stroke-width:0.25;fill-opacity:0" d="M {scale(x1, midpoint_x + ep_x, rx)} {scale(y1, midpoint_y + ep_y, rx) + 120} L {scale(x1, midpoint_x, rx)} {scale(y1, midpoint_y, rx) + 120}" />')

                        midpoint_edge_x = midpoint_x + math.cos(midpoint_angle)
                        midpoint_edge_y = midpoint_y - math.sin(midpoint_angle)
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="1.25" cx="{scale(x1, midpoint_edge_x, rx)}" cy="{scale(y1, midpoint_edge_y, rx) + 120}" />')
                        print(f'<path style="stroke:#000000;stroke-width:0.25;fill-opacity:0" d="M {scale(x1, midpoint_edge_x, rx)} {scale(y1, midpoint_edge_y, rx) + 120} L {scale(x1, midpoint_x, rx)} {scale(y1, midpoint_y, rx) + 120}" />')

                        point_y_x = midpoint_x + (math.cos(midpoint_angle) * fig_y)
                        point_y_y = midpoint_y - (math.sin(midpoint_angle) * fig_y)
                        # y
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="1" cx="{scale(x1, point_y_x, rx)}" cy="{scale(y1, point_y_y, rx) + 120}" />')
                        print(f'<path style="stroke:#000000;stroke-width:0.15;fill-opacity:0" d="M {scale(x1, midpoint_x + sp_x, rx)} {scale(y1, midpoint_y + sp_y, rx) + 120} L {scale(x1, point_y_x, rx)} {scale(y1, point_y_y, rx) + 120}" />')

                        # Control handles - red for start, black for end
                        print(f'<path style="stroke:#ff0000;stroke-width:0.25;fill-opacity:0" d="M {scale(x1, start_2L_x, rx)} {scale(y1, start_2L_y, rx) + 120} L {scale(x1, midpoint_x + sp_x, rx)} {scale(y1, midpoint_y + sp_y, rx) + 120}" />')
                        print(f'<path style="stroke:#000000;stroke-width:0.25;fill-opacity:0" d="M {scale(x1, end_2L_x, rx)} {scale(y1, end_2L_y, rx) + 120} L {scale(x1, midpoint_x + ep_x, rx)} {scale(y1, midpoint_y + ep_y, rx) + 120}" />')
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="0.5" cx="{scale(x1, start_2L_x, rx)}" cy="{scale(y1, start_2L_y, rx) + 120}" />')
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="0.5" cx="{scale(x1, end_2L_x, rx)}" cy="{scale(y1, end_2L_y, rx) + 120}" />')

                        # The actual bezier
                        print(f'<path style="stroke:#0000ff;stroke-width:0.25;fill-opacity:0" ' +
                              f'd="M {scale(x1, midpoint_x + sp_x, rx)} {scale(y1, midpoint_y + sp_y, rx) + 120} ' +
                              f'C {scale(x1, start_2L_x, rx)} {scale(y1, start_2L_y, rx) + 120} ' + 
                              f'{scale(x1, end_2L_x, rx)} {scale(y1, end_2L_y, rx) + 120} ' + 
                              f'{scale(x1, midpoint_x + ep_x, rx)} {scale(y1, midpoint_y + ep_y, rx) + 120} Z" />')
                        
                        # Test dots
                        print(f'<circle style="fill:#0000ff;fill-opacity:1" r="1" cx="{r_scontrol[0]}" cy="{r_scontrol[1]}" />')
                        print(f'<circle style="fill:#0000ff;fill-opacity:1" r="1" cx="{r_econtrol[0]}" cy="{r_econtrol[1]}" />')

                        # Un-rotate/scale start and end pos
                        r_seg_start_pos = rotate(last_pos, (scale(x1, midpoint_x + sp_x, rx), scale(y1, midpoint_y + sp_y, ry)), angle)
                        r_seg_end_pos = rotate(last_pos, (scale(x1, midpoint_x + ep_x, rx), scale(y1, midpoint_y + ep_y, ry)), angle)
                        print(f'<path style="stroke:#000000;stroke-width:0.15;fill-opacity:0" d="M {r_scontrol[0]} {r_scontrol[1]} L {r_seg_start_pos[0]} {r_seg_start_pos[1]}" />')
                        print(f'<path style="stroke:#000000;stroke-width:0.15;fill-opacity:0" d="M {r_econtrol[0]} {r_econtrol[1]} L {r_seg_end_pos[0]} {r_seg_end_pos[1]}" />')

                        # Lines for L and half L
                        test_L_x = midpoint_x + sp_x + (math.cos(start_angle + adjustment) * fig_2L / 2)
                        test_L_y = midpoint_y + sp_y + (-math.sin(start_angle + adjustment) * fig_2L / 2)
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="0.25" cx="{scale(x1, test_L_x, rx)}" cy="{scale(y1, test_L_y, rx) + 120}" />')

                        test_L_x = midpoint_x + sp_x + (math.cos(start_angle + adjustment) * 3 * fig_2L / 4)
                        test_L_y = midpoint_y + sp_y + (-math.sin(start_angle + adjustment) * 3 * fig_2L / 4)
                        print(f'<circle style="fill:#000000;fill-opacity:1" r="0.25" cx="{scale(x1, test_L_x, rx)}" cy="{scale(y1, test_L_y, rx) + 120}" />')


                        # The actual bezier in the original position
                        #print(f'<path style="stroke:#0000ff;stroke-width:0.15;fill-opacity:0" ' +
                        #      f'd="M {scale(x1, midpoint_x + sp_x, rx)} {scale(y1, midpoint_y + sp_y, ry)} ' +
                        #      f'C {r_scontrol[0]} {r_scontrol[1]} ' + 
                        #      f'{r_econtrol[0]} {r_econtrol[1]} ' + 
                        #      f'{scale(x1, midpoint_x + ep_x, rx)} {scale(y1, midpoint_y + ep_y, ry)} Z" />')

                set_last_pos(end_pos[0], end_pos[1])
                #print(f"<!-- New current point is {last_pos} -->")

            if debug:
                # Include original arc in resulting image
                new_commands.append(c)

            # Build the bezier curve command
            bezier_path = ["C"]
            for b in beziers:
                bezier_path = bezier_path + b
            new_commands.append(bezier_path)
        else:
            new_commands.append(c)
        
        first_command = False

    commands = new_commands
    
    #print(bezier_path)
    command_strings = []
    for c in commands:
        command_strings.append(f"{c[0]} {' '.join([optional_p(x) for x in c[1:]])}")
    #print(command_strings)
    
    return " ".join(command_strings)

class SVGHandler(ContentHandler):
    def startElement(self, name, attrs):
        attributes = []
        for attr, val in attrs.items():
            if name.lower() == "path" and attr.lower() == "d":
                val = fix_path(val)
            attributes.append(f'{attr}="{val}"')
        
            
        print(f'<{name} {" ".join(attributes)}>')
        

    def endElement(self, name):
        print(f'</{name}>')

    def characters(self, content):
        if content.strip() != '':
            print(content)

print('<?xml version="1.0" encoding="UTF-8"?>')
parse(sys.argv[1], SVGHandler())

