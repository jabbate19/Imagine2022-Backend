from operator import itemgetter
from math import degrees, radians, sin, cos, acos, atan2, pi

from geographiclib.geodesic import Geodesic
Geo = Geodesic.WGS84

from geographiclib.constants import Constants
#WGS84_a : equatorial radius of the ellipsoid, in metres
#WGS84_f : flattening of the ellipsoid
#WGS84_e2: eccentricity squared of the ellipsoid
WGS84_a, WGS84_f = Constants.WGS84_a, Constants.WGS84_f
WGS84_e2 = WGS84_f * (2 - WGS84_f)

#60 international nautical miles in metres
metres_per_deg = 111120.0

# Tolerance in calculated distances, in metres.
# Try adjusting this value if the geo_newton function fails to converge.
distance_tol = 1E-8

# Tolerance in calculated positions, in degrees.
position_tol = 5E-10

# Crude floating-point equality test
def almost_equal(a, b, tol=5E-12):
    return abs(a - b) < tol


def normalize_lon(x, a):
    ''' reduce longitude to range -a <= x < a '''
    return (x + a) % (2 * a) - a


class LatLong(object):
    ''' latitude & longitude in degrees & radians.
        Also colatitude in radians.
    '''
    def __init__(self, lat, lon, in_radians=False):
        ''' Initialize with latitude and longitude,
            in either radians or degrees
        '''
        if in_radians:
            lon = normalize_lon(lon, pi)
            self.lat = lat
            self.colat = 0.5 * pi - lat
            self.lon = lon
            self.dlat = degrees(lat)
            self.dlon = degrees(lon)
        else:
            lon = normalize_lon(lon, 180.0)
            self.lat = radians(lat)
            self.colat = radians(90.0 - lat)
            self.lon = radians(lon)
            self.dlat = lat
            self.dlon = lon

    def __repr__(self):
        return 'LatLong(%.12f, %.12f, in_radians=True)' % (self.lat, self.lon)

    def __str__(self):
        return 'Lat: %.9f, Lon: %.9f' % (self.dlat, self.dlon)

# -------------------------------------------------------------------
# Spherical triangle solutions based on the spherical cos rule
# cos(c) = cos(a) * cos(b) + sin(a) * sin(b) * cos(C)
# Side calculations use functions that are less susceptible
# to round-off errors, from
# https://en.wikipedia.org/wiki/Solution_of_triangles#Two_sides_and_the_included_angle_given

def opp_angle(a, b, c):
    ''' Given sides a, b & c find C, the angle opposite side c '''
    t = (cos(c) - cos(a) * cos(b)) / (sin(a) * sin(b))
    try:
        C = acos(t)
    except ValueError:
        # "Reflect" t if it's out of bounds due to rounding errors.
        # This happens roughly 1% of the time, on average.
        if t > 1.0:
            t = 2.0 - t
        elif t < -1.0:
            t = -2.0 - t
        C = acos(t)
    return C


def opp_side(a, b, C):
    ''' Find side c given sides a, b and the included angle C '''
    sa, ca = sin(a), cos(a)
    sb, cb = sin(b), cos(b)
    sC, cC = sin(C), cos(C)

    u = sa * cb - ca * sb * cC
    v = sb * sC
    num = (u ** 2 + v ** 2) ** 0.5
    den = ca * cb + sa * sb * cC
    return atan2(num, den)

def opp_side_azi(a, b, C):
    ''' Find side c given sides a, b and the included angle C
        Also find angle A
    '''
    sa, ca = sin(a), cos(a)
    sb, cb = sin(b), cos(b)
    sC, cC = sin(C), cos(C)

    u = sa * cb - ca * sb * cC
    v = sb * sC
    num = (u ** 2 + v ** 2) ** 0.5
    den = ca * cb + sa * sb * cC

    # side c, angle A
    return atan2(num, den), atan2(v, u)


def gc_distance(p, q):
    ''' The great circle distance between two points '''
    return opp_side(p.colat, q.colat, q.lon - p.lon)

def gc_distance_azi(p, q):
    ''' The great circle distance between two points & azimuth at p '''
    return opp_side_azi(p.colat, q.colat, q.lon - p.lon)


def azi_dist(p, azi, dist):
    ''' Find point x given point p, azimuth px, and distance px '''
    x_colat, delta = opp_side_azi(p.colat, dist, azi)
    x = LatLong(0.5 * pi - x_colat, p.lon + delta, in_radians=True)
    return x


def tri_test(*sides):
    ''' Triangle inequality.
        Check that the longest side is not greater than
        the sum of the other 2 sides.
        Return None if triangle ok, otherwise return
        the longest side's index & length and the excess.
    '''
    i, m = max(enumerate(sides), key=itemgetter(1))
    # m > (a + b) -> 2*m > (m + a + b)
    excess = 2 * m - sum(sides)
    if excess > 0:
        return i, m, excess
    return None


def gc_triangulate(a, ax_dist, b, bx_dist, verbose=0):
    ''' Great circle distance triangulation
        Given points a & b find the two points x0 & x1 that
        are both ax_dist & bx_dist, respectively, from a & b.
        Distances are in degrees.
    '''
    # Distance AB, the base of the OAB triangle
    ab_dist, ab_azi = gc_distance_azi(a, b)
    ab_dist_deg = degrees(ab_dist)
    if verbose > 1:
        print('AB distance: %f\nAB azimuth: %f' % 
            (ab_dist_deg, degrees(ab_azi)))

    # Make sure sides of ABX obey triangle inequality
    bad = tri_test(ab_dist_deg, ax_dist, bx_dist)
    if bad is not None:
        print('Bad gc side length %d: %f, excess = %f' % bad)
        raise ValueError

    # Now we need the distance args in radians
    ax_dist, bx_dist = radians(ax_dist), radians(bx_dist)

    # Angle BAX
    bax = opp_angle(ax_dist, ab_dist, bx_dist)
    if verbose > 1:
        print('Angle BAX: %f\n' % degrees(bax))

    # OAX triangle, towards the pole
    ax_azi = ab_azi - bax
    if verbose > 1:
        print('AX0 azimuth: %f' % degrees(ax_azi))
    x0 = azi_dist(a, ax_azi, ax_dist)

    # OAX triangle, away from the pole
    ax_azi = ab_azi + bax
    if verbose > 1:
        print('AX1 azimuth: %f\n' % degrees(ax_azi))
    x1 = azi_dist(a, ax_azi, ax_dist)
    return x0, x1

# -------------------------------------------------------------------
# Geodesic stuff using geographiclib & the WGS84 ellipsoid

# default keys returned by Geo.Inverse
# ['a12', 'azi1', 'azi2', 'lat1', 'lat2', 'lon1', 'lon2', 's12']
# full set of keys
# ['M12', 'M21', 'S12', 'a12', 'azi1', 'azi2',
# 'lat1', 'lat2', 'lon1', 'lon2', 'm12', 's12']

def geo_distance(p, q):
    ''' The geodesic distance between two points '''
    return Geo.Inverse(p.dlat, p.dlon, q.dlat, q.dlon)['s12']


# Meridional radius of curvature and Radius of circle of latitude,
# multiplied by (pi / 180.0) to simplify calculation of partial derivatives
# of geodesic length wrt latitude & longitude in degrees
def rho_R(lat):
    lat = radians(lat)
    w2 = 1.0 - WGS84_e2 * sin(lat) ** 2
    w = w2 ** 0.5

    # Meridional radius of curvature
    rho = WGS84_a * (1.0 - WGS84_e2) / (w * w2)

    # Radius of circle of latitude; a / w is the normal radius of curvature
    R = WGS84_a * cos(lat) / w
    return radians(rho), radians(R)


def normalize_lat_lon(lat, lon):
    ''' Fix latitude & longitude if abs(lat) > 90 degrees,
        i.e., the point has gone over the pole.
        Also normalize longitude to -180 <= x < 180
    '''
    if lat > 90.0:
        lat = 180.0 - lat
        lon = -lon
    elif lat < -90.0:
        lat = -180.0 - lat
        lon = -lon
    lon = normalize_lon(lon, 180.0)
    return lat, lon


def geo_newton(a, b, x, ax_dist, bx_dist, verbose=0):
    ''' Solve a pair of simultaneous geodesic distance equations
        using Newton's method.
        Refine an initial approximation of point x such that
        the distance from point a to x is ax_dist, and
        the distance from point b to x is bx_dist
    '''
    # Original approximations
    x_dlat, x_dlon = x.dlat, x.dlon

    # Typically, 4 or 5 loops are adequate.
    for i in range(30):
        # Find geodesic distance from a to x, & azimuth at x
        d = Geo.Inverse(a.dlat, a.dlon, x_dlat, x_dlon)
        f0, a_azi = d['s12'], d['azi2']

        # Find geodesic distance from b to x, & azimuth at x
        d = Geo.Inverse(b.dlat, b.dlon, x_dlat, x_dlon)
        g0, b_azi = d['s12'], d['azi2']

        #Current errors in f & g
        delta_f = ax_dist - f0
        delta_g = bx_dist - g0
        if verbose > 1:
            print(i, ': delta_f =', delta_f, ', delta_g =', delta_g)

        if (almost_equal(delta_f, 0, distance_tol) and
            almost_equal(delta_g, 0, distance_tol)):
            if verbose and i > 9: print('Loops =', i)
            break

        # Calculate partial derivatives of f & g
        # wrt latitude & longitude in degrees
        a_azi = radians(a_azi)
        b_azi = radians(b_azi)
        rho, R = rho_R(x_dlat)
        f_lat = rho * cos(a_azi)
        g_lat = rho * cos(b_azi)
        f_lon = R * sin(a_azi)
        g_lon = R * sin(b_azi)

        # Generate new approximations of x_dlat & x_dlon
        den = f_lat * g_lon - f_lon * g_lat
        dd_lat = delta_f * g_lon - f_lon * delta_g
        dd_lon = f_lat * delta_g - delta_f * g_lat
        x_dlat += dd_lat / den
        x_dlon += dd_lon / den
        x_dlat, x_dlon = normalize_lat_lon(x_dlat, x_dlon)
    else:
        print('Warning: Newton approximation loop fell through '
        'without finding a solution after %d loops.' % (i + 1))

    return LatLong(x_dlat, x_dlon)


def geo_triangulate(a, ax_dist, b, bx_dist, verbose=0):
    ''' Geodesic Triangulation
        Given points a & b find the two points x0 & x1 that
        are both ax_dist & bx_dist, respectively from a & b.
        Distances are in metres.
    '''
    ab_dist = geo_distance(a, b)
    if verbose:
        print('ab_dist =', ab_dist)

    # Make sure sides of ABX obey triangle inequality
    bad = tri_test(ab_dist, ax_dist, bx_dist)
    if bad is not None:
        #print('Bad geo side length %d: %f, excess = %f' % bad)
        return None

    # Find approximate great circle solutions.
    # Distances need to be given in degrees, so we approximate them
    # using 1 degree = 60 nautical miles
    ax_deg = ax_dist / metres_per_deg
    bx_deg = bx_dist / metres_per_deg
    ab_deg = degrees(gc_distance(a, b))

    # Make sure that the sides of the great circle triangle
    # obey the triangle inequality
    bad = tri_test(ab_deg, ax_deg, bx_deg)
    if bad is not None:
        if verbose > 1:
            print('Bad gc side length after conversion '
                '%d: %f, excess = %f. Adjusting...' % bad)
        i, _, excess = bad
        if i == 1:
            ax_deg -= excess
            bx_deg += excess
        elif i == 2:
            bx_deg -= excess
            ax_deg += excess
        else:
            ax_deg += excess
            bx_deg += excess
        #bad = tri_test(ab_deg, ax_deg, bx_deg)
        #if bad:
            #print 'BAD ', bad
            #print (ab_deg, ax_deg, bx_deg)
            #print a, ax_dist, b, bx_dist

    x0, x1 = gc_triangulate(a, ax_deg,  b, bx_deg, verbose=verbose)

    if verbose:
        ax = geo_distance(a, x0)
        bx = geo_distance(b, x0)
        print('\nInitial X0:', x0)
        print('ax0 =', ax, ', error =', ax - ax_dist)
        print('bx0 =', bx, ', error =', bx - bx_dist)

    # Use Newton's method to get the true position of x0
    x0 = geo_newton(a, b, x0, ax_dist, bx_dist, verbose=verbose)

    if verbose:
        ax = geo_distance(a, x1)
        bx = geo_distance(b, x1)
        print('\nInitial X1:', x1)
        print('ax1 =', ax, ', error =', ax - ax_dist)
        print('bx1 =', bx, ', error =', bx - bx_dist)
        print()

    # Use Newton's method to get the true position of x1
    x1 = geo_newton(a, b, x1, ax_dist, bx_dist, verbose=verbose)
    return x0, x1