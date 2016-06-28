import json
import math

__author__ = 'apostol3'


class Map:
    def __init__(self, w, h):
        self.max_time = 120
        self.size = (w, h)
        self.walls = []
        self.headline = []
        self.cars = []
        self.finish = []
        self.objects = []
        self.car_size = (0.5, 1)

    def start_new_wall(self):
        self.walls.append([])

    def append_wall_point(self, x, y):
        if x > self.size[0] or y > self.size[1]:
            self.start_new_wall()
            return
        self.walls[-1].append((x, y))

    def append_headline_point(self, x, y):
        if x > self.size[0] or y > self.size[1]:
            return
        self.headline.append((x, y))

    def create_car(self, x, y):
        self.cars.clear()
        self.cars.append((x, y, 3 * math.pi / 2))

    def append_finish_point(self, x, y):
        if x > self.size[0] or y > self.size[1]:
            self.finish.clear()
        if len(self.finish) < 2:
            self.finish.append((x, y))
        else:
            self.finish = [(x, y)]

    @staticmethod
    def open_from_file(file):
        f = open(file, 'r')
        doc = json.load(f)
        f.close()
        size = doc['size']
        map = Map(*size)
        map.max_time = doc['max_time']
        map.walls = doc['walls']
        map.finish = doc['finish']
        map.headline = doc['headline']
        map.cars = doc['cars']
        return map

    def save_to_file(self, file):
        filename = open(file, 'w')
        doc = {'size': self.size, 'max_time': self.max_time, 'finish': self.finish,
               'walls': self.walls, 'headline': self.headline, 'cars': self.cars}
        if len(doc['walls']) != 0 and len(doc['walls'][-1]) == 0:
            doc['walls'].pop()

        out_inf = json.dumps(doc, indent=4)
        filename.write(out_inf)
        filename.close()
