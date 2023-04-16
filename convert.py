import sys
import re
from xml.sax import parse
from xml.sax.handler import ContentHandler

import math

def elliptical_arc_to_bezier(x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
    pass

# Rotate a point around an origin point by an angle
def rotate(origin, point, angle):
    dx = point[0] - origin[0]
    dy = point[1] - origin[1]
    dx_ = (dx * math.cos(angle)) + (dy * math.sin(angle))
    dy_ = (dy * math.cos(angle)) + (dx * math.sin(angle))
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

def as_degrees(r):
    return r / math.pi * 180.0

number_re = re.compile('\s*(-?[0-9]*\.[0-9]+|[+-]?[0-9]+e[+-]?[0-9]+|-?[0-9]+),?')
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

    # Pre-process:
    # - Convert multiple moves to move + line
    new_commands = []
    for c in commands:
        cmd = c[0].lower()
        isrelative = c[0].islower()

        # TODO

        new_commands.append(c)
    commands = new_commands

    # Interpret commands
    new_commands = []
    construction_lines = []
    for c in commands:
        cmd = c[0].lower()
        args = c[1:]
        isrelative = c[0].islower()
        
        if cmd == "m":
            # Move to
            if isrelative:
                last_pos = (last_pos[0] + c[1], last_pos[1] + c[2])
                print(f"<!-- Relative move to {last_pos} -->")
            else:
                last_pos = (c[1], c[2])
                print(f"<!-- Absolute move to {last_pos} -->")

        if cmd == "a":
            arcs = args[:]
            while len(arcs) >= 7:
                arc = arcs[:7]
                arcs = arcs[7:]
                # print(last_pos, arc, arcs)

                # Include the original arc for testing purposes:
                new_commands.append(c)

                if isrelative:
                    end_pos = (last_pos[0] + arc[5], last_pos[1] + arc[6])
                    print(f"<!-- Relative arc from {last_pos} to {end_pos} -->")
                else:
                    end_pos = (arc[5], arc[6])
                    print(f"<!-- Absolute arc from {last_pos} to {end_pos} -->")

                rx = arc[0]
                ry = arc[1]
                angle = arc[2]
                large_arc_flag = int(arc[3])
                sweep_flag = int(arc[4])

                # Which side the circle's centre point will be on
                side = bool(large_arc_flag) ^ bool(sweep_flag)

                # Eliminate "angle" variable by rotating everything (which is just the end point) around the start point.
                # Now r1 and r2 should line up with x and y axes
                rotated_end_point = rotate(last_pos, end_pos, -angle)
                
                #construction_lines.append(["fill:#0000ff;fill-opacity:0.25", "M", last_pos[0], last_pos[1] + 120, 
                #    "A", rx, ry, 0, large_arc_flag, sweep_flag, rotated_end_point[0], rotated_end_point[1] + 120])
                
                # Scale the ellipse to r1 = 1, r2 = 1 (circle)
                rx_scale = 1.0 / rx
                ry_scale = 1.0 / ry
                print(f"<!-- Ellipse scales are {(rx, ry)} -->")

                scaled_end_point_x = scale(last_pos[0], rotated_end_point[0], rx_scale)
                scaled_end_point_y = scale(last_pos[1], rotated_end_point[1], ry_scale)
                scaled_end_point = (scaled_end_point_x, scaled_end_point_y)

                p1 = last_pos
                x1 = p1[0]
                y1 = p1[1]

                p2 = scaled_end_point
                x2 = p2[0]
                y2 = p2[1]

                # Distance between the two points:
                q = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))
                print(f"<!-- Distance between p1 and p2 is {q} -->")
                # Linear midpoint on line p1,p2
                x3 = (x1 + x2) / 2
                y3 = (y1 + y2) / 2

                # Circle 1:
                if side == False:
                    midpoint_x = x3 - math.sqrt(1 - math.pow(q / 2, 2)) * (y1 - y2) / q
                    midpoint_y = y3 - math.sqrt(1 - math.pow(q / 2, 2)) * (x2 - x1) / q
                else:
                    midpoint_x = x3 + math.sqrt(1 - math.pow(q / 2, 2)) * (y1 - y2) / q
                    midpoint_y = y3 + math.sqrt(1 - math.pow(q / 2, 2)) * (x2 - x1) / q
                print(f"<!-- Circle midpoint is {(midpoint_x, midpoint_y)} -->")
                print(f"<!-- Scaled midpoint is {(scale(x1, midpoint_x, rx), scale(y1, midpoint_y, ry))} -->")

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
                print(f"<!-- point 1 original coords: {p1} -->")
                print(f"<!-- point 1 relative coords: {rel_x1:.4f}, {rel_y1:.4f} -->")
                #p1_angle = math.asin(rel_y1) if side else (math.pi + math.asin(rel_y1))
                # Y is negative because SVG's coords are upside down compared to python's math module's
                p1_angle = math.atan2(-rel_y1, rel_x1) % (2 * math.pi)
                print(f"<!-- point 1 angle: {as_degrees(p1_angle):.4f} -->")

                # point 2 relative to origin
                rel_x2 = x2 - midpoint_x
                rel_y2 = y2 - midpoint_y
                print(f"<!-- point 2 original coords: {p2} -->")
                print(f"<!-- point 2 relative coords: {rel_x2:.4f}, {rel_y2:.4f} -->")
                #p2_angle = math.asin(rel_y2) if side else (math.pi + math.asin(rel_y2))
                p2_angle = math.atan2(-rel_y2, rel_x2) % (2 * math.pi)
                print(f"<!-- point 2 angle: {as_degrees(p2_angle):.4f} -->")


                # Divide the arc up into 90-degree segments
                segments = []
                segment_start_angle = p1_angle

                if sweep_flag:
                    angle_remain = (p1_angle if p1_angle > p2_angle else ((2 * math.pi) + p1_angle)) - p2_angle
                else:
                    angle_remain = (p2_angle if p2_angle > p1_angle else ((2 * math.pi) + p2_angle)) - p1_angle

                print(f"<!-- total angle: {as_degrees(angle_remain)} -->")
                while angle_remain > 0:
                    seg_angle = min(angle_remain, math.pi / 2)
                    segment_end_angle = segment_start_angle - seg_angle if sweep_flag else segment_start_angle + seg_angle

                    print(f"<!--     segment with angle {as_degrees(seg_angle)} -->")
                    print(f"<!--         start angle {as_degrees(segment_start_angle)} to {as_degrees(segment_end_angle)}-->")

                    # Start angle, end angle
                    segments.append((segment_start_angle, segment_end_angle))

                    # Ready for next segment
                    segment_start_angle = segment_end_angle
                    angle_remain -= seg_angle

                # Generate cubic beziers for the segments
                print(f"<!-- Generating {len(segments)} cubic beziers: -->")
                for start_angle, end_angle in segments:
                    print(f"<!--     From {as_degrees(start_angle)} to {as_degrees(end_angle)}: -->")

                    # Start point of control handle 1 line is on circumference of circle at start of arc
                    # Tangent of control handle 1 line is tangent of circle angle

                    # Start point of control handle 2 line is on circumference of circle at end of arc
                    # Tangent of control handle 2 line is tangent of circle angle

                    # Find midpoint of arc (on circle)
                    # Find tangent of midpoint

                    # Intersection of midpoint line and control handle 1 line is halfway point of control handle 1 line
                    # Find length of line from intersecting point to start of control handle 1 line
                    # Extend line to double this length, that is control handle 1 point

                    # Intersection of midpoint line and control handle 2 line is halfway point of control handle 2 line
                    # Find length of line from intersecting point to start of control handle 2 line
                    # Extend line to double this length, that is control handle 2 point

                # TODO: scale the ellipse back to original r1, r2 values

                # TODO: rotate the ellipse back to its original angle

                # print("<!-- params:", last_pos[0], last_pos[1], arc[0], arc[1], arc[2], arc[3], arc[4], end_pos[0], end_pos[1], "-->")
                #beziers = elliptical_arc_to_bezier(last_pos[0], last_pos[1], arc[0], arc[1], arc[2], arc[3], arc[4], end_pos[0], end_pos[1])
                #for b in beziers:
                #    print("<!-- ... Cubic bezier curve from", last_pos, "to", end_pos, "with control points", 
                #          (b[2], b[3]), (b[4], b[5]), "-->")
                    
                #    new_commands.append(["E", b[0], b[1], b[2], b[3], b[4], b[5]])
            



                last_pos = end_pos

            #new_commands.append(c)
        else:
            new_commands.append(c)
    commands = new_commands
       
    command_strings = []
    for c in commands:
        command_strings.append(f"{c[0]} {' '.join([optional_p(x) for x in c[1:]])}")
    
    # Emit the construction lines in blue, with origin (0, 120)
    for path in construction_lines:
        print(f"<path style=\"{path[0]}\" d=\"{' '.join([str(p) for p in path[1:]])} Z\"/>")
    
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

