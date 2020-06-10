from PIL import Image, ImageDraw
from progress.bar import Bar
import sys
if sys.platform == 'win32':
    from tkinter.filedialog import askopenfiles
    from tkinter import Tk
    root = Tk()
    root.withdraw()
else:
    print("You're using a non-Windows environment. Certain methods will not be available.")

"""
See the README.md on Github for usage
https://github.com/Zciurus-Alt-Del/Geodata_visualizer
"""


class Geo:
    def __init__(self, asc_file):
        self._asc_file = asc_file

        desc = self._read_descriptor()
        self._nodata_value = desc['NODATA_VALUE']
        self._file_y_len = desc['NROWS']
        self._file_x_len = desc['NCOLS']
        self._file_cellsize = desc['CELLSIZE']
        self._descriptor_len = desc['descriptor_len']

        self._array = self._read_array()
        self._value_range = None

        self._draw = None
        self._image = None

    def _read_descriptor(self):
        ret = {}
        with open(self._asc_file, 'r') as f:
            line = ''
            desc_len = -1
            while len(line) < 50:
                desc_len += 1
                line = f.readline()
                while '  ' in line:
                    line = line.replace('  ',' ')
                kv = line.split(' ')
                ret[kv[0]] = int(kv[1])
        ret['descriptor_len'] = desc_len
        return ret

    def _read(self):
        #TODO eigene Read, die den descriptor weglässt
        f = open(self._asc_file, 'r')
        [f.readline() for x in range(self._descriptor_len)]
        return f

    def _read_array(self):
        data = []
        bar = Bar('Reading Data', max=self._file_y_len)
        with self._read() as f:
            for y in range(self._file_y_len):
                line = f.readline()
                data.append([float(x) for x in line.split(' ')])
                bar.next()
        bar.finish()
        return data

    @staticmethod
    def _val_as_rgb(value, gradient_interval):
        """
        Überträgt den Wert 'value' aus dem Intervall [minimum, maximum] auf das RGB-Spektrum
        :param value: Diesen Wert übertragen
        :return: r, g, b
        """
        minimum, maximum = float(gradient_interval[0]), float(gradient_interval[1])
        ratio = 2 * (value - minimum) / (maximum - minimum)
        b = int(max(0, 255 * (1 - ratio)))
        r = int(max(0, 255 * (ratio - 1)))
        g = 255 - b - r
        return r, g, b

    def _to_debug_txt(self, filename, array='_array'):
        if array == "_array":
            array = self._array
        f = open(filename, 'w+')
        bar = Bar('Writing', max=self._file_y_len)
        for line in array:
            txtline = ""
            for point in line:
                txtline += str(point) + " "
            txtline += "\n"
            f.write(txtline)
            bar.next()
        bar.finish()
        f.close()

    @staticmethod
    def images_to_gif(gifname, duration=100, loop=0):
        files = [x.name for x in askopenfiles()]
        imgfiles = [Image.open(x, 'r') for x in files]
        imgfiles[0].save(gifname, format='GIF', append_images=imgfiles[1:], save_all=True, duration=duration, loop=loop)
        print(files)

    def _replace_color(self, this_one, with_this_one):
        pixelarray = list(self._image.getdata())
        n_pixel = 0
        bar = Bar('Replacing Colors', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if pixelarray[n_pixel] == this_one:
                    self._draw.point((x,y), with_this_one)
                n_pixel += 1
            bar.next()
        bar.finish()

    def _calc_value_range(self):
        lowest_value = 9999
        highest_value = self._nodata_value + 1

        bar = Bar('Drawing', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field != self._nodata_value:
                    lowest_value = min(lowest_value, field)
                    highest_value = max(highest_value, field)
            bar.next()
        bar.finish()
        self._value_range = (lowest_value, highest_value)
        return lowest_value, highest_value

    def _make_array(self, default_data=False):
        self._array = []
        with self._read() as f:
            bar = Bar('Calculating', max=self._file_y_len)
            for y, stringline in enumerate(f):
                line = [float(x) for x in stringline.split(' ')]
                self._array.append([])
                thisline = self._array[-1]
                for x, field in enumerate(line):
                    thisline.append([field, default_data])
                bar.next()
            bar.finish()

        print('array created with size y',len(self._array),'x',len(self._array[0]))

    def _new_canvas(self, force: bool = False):
        if self._image is None and not force:
            self._image = Image.new('RGBA', (self._file_x_len, self._file_y_len))
            self._draw = ImageDraw.Draw(self._image)

    def export(self, filename, filetype='auto'):
        if filetype == 'auto':
            filetype = filename.split('.')[-1].upper()
        self._image.save(filename, filetype)
        print('Image saved to ', filename)

    def _draw_text(self, text, xy=(0, 0)):
        self._draw.text(xy=xy, text=text)

    def TEMPLATE(self):
        self._new_canvas()
        bar = Bar('Drawing', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                pass
                pass
                self._draw.point((x, y), fill=)
            bar.next()
        bar.finish()

    def avg_height(self):
        """
        The average height of all datapoints.
        :return:
        """
        heightsum = 0
        number_of_values = 0
        self._new_canvas()
        bar = Bar('Drawing', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field != self._nodata_value:
                    heightsum += field
                    number_of_values += 1
            bar.next()
        bar.finish()
        print("Number of data entries: " + str(number_of_values))
        print("Sum: " + str(heightsum))
        avg = heightsum / number_of_values
        print("-> Average: " + str(avg))
        return avg

    def draw_rgb_gradient(self, core_interval: tuple = 'auto', nodata_color=(255, 255, 255)):
        """
        Utilizes the full RGB-spectrum to visualize the given data linearly
        :param core_interval: (lowest, highest) Give all resolution to this interval. 'auto' -> full range
        :param nodata_color:
        :return:
        """
        if core_interval == 'auto':
            core_interval = self._calc_value_range()

        self._new_canvas()
        bar = Bar('Drawing', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field == self._nodata_value:
                    fieldcolor = nodata_color
                else:
                    fieldcolor = Geo._val_as_rgb(field, core_interval)
                self._draw.point((x, y), fill=fieldcolor)
            bar.next()
        bar.finish()


    def draw_grayscale(self):
        """
        Draws the map as a grayscale image
        :return:
        """

        if self._value_range is None:
            self._calc_value_range()
        range = self._value_range
        print('Range was found to be',range, range[1] - range[0])

        self._new_canvas()
        bar = Bar('Drawing', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field != self._nodata_value:
                    linear_value = field/(range[1] - range[0])
                    value = int(linear_value*255)
                else:
                    value = int(range[0])  # evtl = 0?

                color = (value, value, value)
                self._draw.point((x, y), fill=color)

            bar.next()
        bar.finish()

    def draw_sealevel(self, height_above_sealevel,
                      water_color=(132, 194, 251), land_color=(252, 255, 212)):
        """
        Creates a map where every spot lower than the given parameter is filled with water
        :param height_above_sealevel:
        :param water_color: RGB
        :param land_color: RGB
        :return:
        """
        self._new_canvas()
        bar = Bar('Drawing', max=self._file_y_len)

        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field < height_above_sealevel:
                    fieldcolor = water_color
                else:
                    fieldcolor = land_color
                self._draw.point((x, y), fill=fieldcolor)
            bar.next()
        bar.finish()


    def draw_realwater(self, height_above_sealevel: float, water_source_coord = (0, 0), water_color=(132, 194, 251, 255), land_color=(252, 255, 212, 255),
                       name_sealevel_at_top_left: bool = True):
        """
        Creates a more realistic map where spots that are lower than the given parameter and that are connected to the sea are filled.
        :param height_above_sealevel: Cells must lie lower than this height
        :param water_source_coord: Cells must be connected to this coordinate
        :param water_color: RGBA
        :param land_color: RGBA
        :param name_sealevel_at_top_left: Adds the height_above_sealevel as a text in the top left corner
        :return:
        """
        self._new_canvas()
        tempcolor = (0, 255, 0, 255)
        bar = Bar('Drawing', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field < height_above_sealevel:
                    color = tempcolor
                else:
                    color = land_color
                self._draw.point((x, y), color)
            bar.next()
        bar.finish()

        bar = Bar('Flooding', max=100)
        bar.next()
        ImageDraw.floodfill(self._image, (2, 2), value=water_color)
        bar.finish()

        self._replace_color(tempcolor, land_color)
        if name_sealevel_at_top_left:
            self._draw_text(str(height_above_sealevel))

    def generate_obj(self, filename, height_multiplier: float = 1, nodata_replacement: float = 0):
        """
        Converts the dataset to a Wavefront-Obj file.
        :param filename: Export to this filename (automatic extension)
        :param height_multiplier: All heights will be multiplied by this factor.
        :param nodata_replacement: Grid cells with no data will be given this height value.
        :return:
        """
        if '.obj' not in filename:
            filename += '.obj'
        f = open(filename, 'w+')
        f.write('# Generated by a Python Script from "Zciurus-Alt-Del"\no Object.1\n\n# vertices')

        bar = Bar('Writing vertices', max=self._file_y_len)
        for y, line in enumerate(self._array):
            for x, field in enumerate(line):
                if field == self._nodata_value:
                    field = nodata_replacement
                else:
                    field *= height_multiplier
                txtline = f"\nv {x*self._file_cellsize} {field} {y*self._file_cellsize}"  # When describing a vertex in .obj, the second point is the height
                f.write(txtline)
            bar.next()
        bar.finish()
        f.write("\n\n# faces")

        num_of_cells = self._file_y_len * self._file_x_len
        bar = Bar('Writing faces', max=num_of_cells)
        for n in range(num_of_cells - self._file_x_len): # omit last line
            if not n % self._file_x_len == 0: # omit right column
                me = n
                right = n + 1
                bot = n + self._file_x_len
                botright = n + self._file_x_len + 1
                f.write(f"\nf {me} {right} {botright}")
                f.write(f"\nf {me} {botright} {bot}")
            bar.next()
        bar.finish()

        f.close()
        print('Exported to',filename)


germany = Geo('germany1000.asc')
germany.generate_obj('germany_1000_nod9999_hm10', nodata_replacement=-9999,height_multiplier=10)
