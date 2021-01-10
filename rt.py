import math

class Vector3f:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return "[Vector3f x=%f y=%f z=%f]" % (self.x, self.y, self.z)

    def __add__(self, o):
        return Vector3f(self.x+o.x, self.y+o.y, self.z+o.z)

    def __sub__(self, o):
        return Vector3f(self.x-o.x, self.y-o.y, self.z-o.z)

    def __mul__(self, o):
        # scalar product of two vector
        return self.x*o.x+self.y*o.y+self.z*o.z

    def __rmul__(self, o):
        # product with scalar
        return Vector3f(self.x*o, self.y*o, self.z*o)

    def __iter__(self):
        self.prev = None
        return self

    def __next__(self):
        if self.prev == None:
            self.prev = 'x'
            return self.x
        if self.prev == 'x':
            self.prev = 'y'
            return self.y
        if self.prev == 'y':
            self.prev = 'z'
            return self.z
        raise StopIteration

    def normalize(self):
        d = math.sqrt(self.x**2+self.y**2+self.z**2)
        self.x = self.x/d
        self.y = self.y/d
        self.z = self.z/d

    def norm(self):
        return math.sqrt(self.x**2+self.y**2+self.z**2)

class Light:
    def __init__(self,x,y,z,intensity):
        self.position =Vector3f(x,y,z)
        self.intensity = intensity


class Material:
    def __init__(self, diffuse_color, spec, albedo=[1, 0, 0, 0], refractive_index=1):
        self.diffuse_color = diffuse_color
        self.spec = spec
        self.albedo = albedo
        self.refractive_index = refractive_index

class Sphere:
    def __init__(self,x,y,z,r,material):
        self.center = Vector3f(x,y,z)
        self.r = r
        self.material = material

    def rayIntersect(self,orig,dir):
        '''
        Paras:
        orig: the origin of the light 
        dir:  a normed vector showing the direction of light propagation

        Return value (hit,t0)
        hit: a boolean value showing whether intersect
        t0: the distance from orig to intersection point
        '''
        # below are simple geometries
        l = self.center - orig
        tca = l * dir
        minD2 = l*l - tca*tca
        # minD2 is the square of distance between light and center
        if (minD2 > self.r*self.r):
            return (False,None)
        thc = (self.r*self.r - minD2)**0.5
        t0 = tca - thc
        t1 = tca + thc
        # if the origin starts within the sphere, t0 = t1
        if (t0<0):
            t0 = t1
        # meaning intersect in the opposite direction
        if (t0<0):
            return (False,None)
        return (True,t0)


def reflect(I, N):
    return I - 2*(I*N) * N


def refract(I, N, refractive_index):
    cosi = - max(-1, min(1, I*N))
    etai = 1
    etat = refractive_index
    if (cosi < 0):
        cosi = - cosi
        temp = etai
        etai = etat
        etat = temp
        N = Vector3f(0, 0, 0) - N
    eta = etai/etat
    k = 1 - eta*eta*(1-cosi*cosi)
    if (k < 0):
        return Vector3f(0, 0, 0)
    else:
        return eta * I + (cosi*eta-math.sqrt(k)) * N


def scene_intersect(orig, dir, objs):
    '''
    The return value: (hit,N,material)
    hit: if hit an object
    N: the normal vector at intersection
    material: the material of the intersected object
    hit_point: the point where hit
    '''
    minT0 = float("inf")
    N = None
    material = None
    hit_position = None
    for obj in objs:
        (hit, t0) = obj.rayIntersect(orig, dir)
        if (hit and t0 < minT0):
            minT0 = t0
            hit_position = orig+t0*dir
            N = (hit_position - obj.center)
            N.normalize()
            material = obj.material
    chessboard_dist = float("inf")
    if (abs(dir.y) > 0.0001):
        chessboard_d = - (orig.y+4)/dir.y  # chessboard is at y = - 4
        chessboard_hit_position = orig + chessboard_d * dir
        # first hit the chessboard within the board region
        if (chessboard_d > 0 and abs(chessboard_hit_position.x) < 10 and chessboard_hit_position.z < -10 and chessboard_hit_position.z > -30 and chessboard_d < minT0):
            minT0 = chessboard_d
            hit_position = chessboard_hit_position
            N = Vector3f(0, 1, 0)  # for general purpose, consider + -
            chessboard_material_diffuse_color = None
            if ((int(0.5*hit_position.x+1000)+int(0.5+hit_position.z)) & 1):
                chessboard_material_diffuse_color = Vector3f(0.3, 0.3, 0.3)
            else:
                chessboard_material_diffuse_color = Vector3f(0.3, 0.2, 0.1)
            material = Material(chessboard_material_diffuse_color, 50)
    return (minT0 < float("inf"), N, material, hit_position)


def cast_ray(orig, dir, objs, lights, depth=0):
    (hit, N, material, hit_point) = scene_intersect(orig, dir, objs)
    if (depth > 4 or not hit):
        return Vector3f(0.2, 0.7, 0.8)  # background color
    else:
        # reflection term
        reflect_dir = reflect(dir, N)
        reflect_orig = None
        if (reflect_dir*N < 0):
            reflect_orig = hit_point - 0.0001 * N
        else:
            reflect_orig = hit_point + 0.0001 * N
        reflect_color = None
        if not material.albedo[2] == 0:
            reflect_color = cast_ray(
                reflect_orig, reflect_dir, objs, lights, depth+1)
        else:
            reflect_color = Vector3f(0, 0, 0)
        #  refraction term
        refract_dir = refract(dir, N, material.refractive_index)
        refract_orig = None
        if (refract_dir*N < 0):
            refract_orig = hit_point - 0.0001 * N
        else:
            refract_orig = hit_point + 0.0001 * N
        refract_color = None
        if not (material.albedo[3] == 0):
            refract_color = cast_ray(
                refract_orig, refract_dir, objs, lights, depth+1)
        else:
            refract_color = Vector3f(0, 0, 0)

        diffuse_light_intensity = 0
        specular_light_intensity = 0
        for light in lights:
            light_dir = (light.position - hit_point)
            light_dir.normalize()

            # check if objects between light source and hit point
            light_distance = light_dir.norm()
            shadow_orig = None
            if (light_dir*N < 0):
                shadow_orig = hit_point - 0.0001 * N
            else:
                shadow_orig = hit_point + 0.0001 * N
            (shadow_hit, shadow_N, shadow_material, shadow_hit_point) = scene_intersect(
                shadow_orig, light_dir, objs)
            if (shadow_hit and (shadow_hit_point - shadow_orig).norm() < light_distance):
                continue
            intense = max(0, light_dir*N)
            diffuse_light_intensity += light.intensity * intense
            specular_light_intensity += light.intensity * \
                (max(0, reflect(light_dir, N)*dir) ** material.spec)
            # print("one light"+str(diffuse_light_intensity)+" "+ str(specular_light_intensity)+"\n")
        return material.albedo[0] * diffuse_light_intensity * material.diffuse_color + specular_light_intensity*material.albedo[1] * Vector3f(1, 1, 1) + material.albedo[2] * reflect_color + material.albedo[3] * refract_color
    return Vector3f(0.2, 0.7, 0.8)  # background color


def renderRayTracingWithSpecularLight(objs, lights):
    # create a frame buffer: framebuffer[width][height]
    WIDTH = 1000
    HEIGHT = 1000
    HFOV = math.tan(0.5)
    FILENAME = "renderMinimalRayTracing.ppm"
    framebuffer = [[Vector3f(1, 1, 1) for y in range(HEIGHT)]
                   for x in range(WIDTH)]
    # manipulate the frame buffer
    ori = Vector3f(0, 0, 0)  # the position of camera
    for x in range(WIDTH):
        for y in range(HEIGHT):
            # this calculation of dir is just a approxiamation,
            # the filed of view indeed is not a cone and other geometric factors are not concerned
            # any way, it's still enough for this tiny project
            dir_x = (2*x/WIDTH-1)*HFOV*WIDTH/HEIGHT
            dir_y = (2*y/HEIGHT-1)*HFOV
            dir = Vector3f(dir_x, dir_y, -1)
            dir.normalize()
            framebuffer[x][y] = cast_ray(ori, dir, objs, lights)
    # Save it on disk
    imageFile = open(FILENAME, "w")
    imageFile.write("P3\n")
    imageFile.write("%i %i \n255\n" % (HEIGHT, WIDTH))
    for x in range(WIDTH):
        for y in range(HEIGHT):
            for color in framebuffer[x][y]:
                temp = int(255 * max(0, min(color, 1)))
                imageFile.write(str(temp)+" ")
    imageFile.close()


ivory = Material(Vector3f(0.4, 0.4, 0.3), 50, [0.6, 0.3, 0.1, 0], 1)
red_rubber = Material(Vector3f(0.3, 0.1, 0.1), 10, [0.9, 0.1, 0, 0], 1)
mirror = Material(Vector3f(1, 1, 1), 1425, [0, 10, 0.8, 0], 1)
glass = Material(Vector3f(0.6, 0.7, 0.8), 125, [0.0, 0.5, 0.1, 0.8], 1.5)
objs = [Sphere(-3, 0, -16, 2, ivory), Sphere(-1, -1.5, -12, 2, glass),
        Sphere(1.5, -0.5, -18, 3, red_rubber), Sphere(7, 5, -18, 4, mirror)]
lights = [Light(-20, 20, 20, 1.5), Light(30, 50, -25, 1.8),
          Light(30, 20, 30, 1.7), Light(0, 0, 1, 2)]
renderRayTracingWithSpecularLight(objs, lights)
