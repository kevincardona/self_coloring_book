from PIL import Image
import time, shutil, glob, os, random, math, imageio

# TODO: Env variables/interface?

# GENERAL SETTINGS
OVERWRITE = False
OFF_WHITE = True
WHITE_ACCEPTANCE = 200

# GIF SETTINGS
GIF = True
GIF_DURATION = 15
GIF_TAIL = 2
GIF_FPS = 10
gif_image_index = 0

# COLOR SETTINGS
COLOR_VARIANCE_R = 100
COLOR_VARIANCE_G = 100
COLOR_VARIANCE_B = 100
BASE_COLOR = (125,125,125)

colored = {}
whitespaces = []

def get_pixel_value(image, coords):
  w, h = image.size
  if (coords[0] >= 0 and coords[0] < w and coords[1] >= 0 and coords[1] < h):
    return coords
  return None

def should_be_colored(coord, color):
  if colored.get(coord):
    return False
  result = True
  if OFF_WHITE:
    result = result and color[0] >= WHITE_ACCEPTANCE 
    result = result and color[1] >= WHITE_ACCEPTANCE 
    result = result and color[2] >= WHITE_ACCEPTANCE
  else:
    result = color == (255, 255, 255)
  colored[coord] = True
  return result
      
def get_uncolored_around_cursor(image, x, y):
  uncolored = [0,0,0,0]
  # Checks Pixels Up, Down, Left, Right
  uncolored[0] = get_pixel_value(image, (x, y-1))
  uncolored[1] = get_pixel_value(image, (x, y+1))
  uncolored[2] = get_pixel_value(image, (x-1, y))
  uncolored[3] = get_pixel_value(image, (x+1, y))
  return uncolored
  
def color_region(image, x, y, color):
  pixel_map = image.load()
  # Color current pixel
  pixel_map[x,y] = color
  # Take a snapshot of the current image for GIF
  gif_snapshot(image)
  # Mark surrounding pixels to be colored + add to queue to search around surrounding pixels
  uncolored = get_uncolored_around_cursor(image, x, y)
  for pixel in uncolored:
    if pixel != None:
      if should_be_colored(pixel, image.getpixel(pixel)):
        whitespaces.append(pixel)

def color_image(image):
  for x in range(image.size[0]):
    for y in range(image.size[1]):
      # TODO: Actually setup color variance properly
      if should_be_colored((x,y), image.getpixel((x, y))):
        r = random.randint(0, COLOR_VARIANCE_R) + BASE_COLOR[0]
        g = random.randint(0, COLOR_VARIANCE_G) + BASE_COLOR[1]
        b = random.randint(0, COLOR_VARIANCE_B) + BASE_COLOR[2]
        color = (r,g,b)
        color_region(image, x, y, color)
        while len(whitespaces) != 0:
          current_pixel = whitespaces.pop()
          color_region(image, current_pixel[0], current_pixel[1], color)

def color_images():
  for filename in glob.glob('uncolored/*'):
    start_time = time.time()
    image = Image.open(filename).convert('RGB')
    name = filename.split('/')[1].split('.')[-2]
    if (glob.glob('colored/*.png').__contains__(f'colored/{name}.png') == False or OVERWRITE):
      color_image(image)
      image.save(f'colored/{name}.png')
      total_time = time.time() - start_time
      print(f'Created {name}.png in {total_time} seconds!')
      generate_gif(name, image)
    else:
      print(f'{name} has already been colored!')

def generate_gif(name, image):
  if not GIF:
    return
  global GIF_FPS, GIF_TAIL
  start_time = time.time()
  w, h = image.size
  with imageio.get_writer(f'generated_gifs/{name}.gif', mode='I', fps = GIF_FPS) as writer:
    all_files = sorted(glob.glob(f'gif_images/*'), key=os.path.getmtime)
    for filename in all_files:
      image = imageio.imread(filename)
      writer.append_data(image)
    for i in range(GIF_TAIL * GIF_FPS):
      image = imageio.imread(all_files[-1])
      writer.append_data(image)
  total_time = time.time() - start_time
  print(f'Created {name}.gif in {total_time} seconds!')
  clean_directories()

def gif_snapshot(image):
  if not GIF:
    return
  global gif_image_index, GIF_DURATION
  # Calculates how many pixel changes per frame needed to match GIF_FPS + Duration
  if gif_image_index % math.ceil(image.size[0] * image.size[1] / GIF_FPS / GIF_DURATION) == 0:
    image.save(f'gif_images/{gif_image_index}.png')
  gif_image_index += 1

def clean_directories():
  if os.path.exists('gif_images'):
    shutil.rmtree('gif_images')
  os.mkdir('gif_images')
  if os.path.exists('generated_gifs') == False:
    os.mkdir('generated_gifs')
  if os.path.exists('colored') == False:
    os.mkdir('colored')

if __name__ == "__main__":
  clean_directories()
  color_images()