#!/usr/bin/env python

"""
    Snake Game
    Peter Mekis, 2021

    Help the snake(s) grow longer by moving around and eating donuts.
    Control: arrow keys or WASD.

    A Pygame project with dynamic object generation. It uses a grid of coordinates (instead of the whole canvas) for placing and moving sprites. Grid coordinates are used for collision detection rather than Pygame's collision detection method.

    The player wins by completing 5 levels. Each level is a maze, with increasing complexity.

    In one player mode score is proportional to the length of the snake. Two player mode is cooperative; score is proportional to the sum of the lengths of the snakes.

    There are three difficulties: in Easy you have to collect  60 points to complete a level; in Medium 120; and in Hard 180.

    Ideas to improve:
    - better graphics (replace the png files)
    - better mazes (replace the txt files)
    - multiplayer mode with self-controlling snake bots
    - fps grows with the snake
    - different donuts (grower, shrinker, poisonous, duplicator, etc.)
    - control with relative directions (turn left, turn right)
    - sounds

    The game window is scaled by a ratio given by the scale parameter calling the game. The dimensions are as follows:
    - the grid is 31*23
    - the gridstep is 30
    - there is half a gridstep margin at each side
    - if scale = 1.0, the game window is sized 960*720
      width = (0.5+31+0.5) * 30
      height: (0.5+23+0.5) * 30
    - if scale = 0.5, the game window is sized 480*360
      which fits in a web browser window when played in replit

    Every image and text is scaled along with the grid.

"""

# These are the usual packages, necessary in every similar game.
import pygame as pg
import sys
import random as r

"""
    This is a basic class for simple sprites. It can be used in various game projects. Specific sprites will be subclasses of it, inheriting its attributes ans methods.
"""
class Sprite():
    def __init__(self, scale, costume_names, x, y, vx = 0, vy = 0):
        raw_costumes = [pg.image.load(name + ".png") for name in costume_names]
        self.costumes = [pg.transform.rotozoom(s, 0, scale) for s in raw_costumes]
        self.costume = self.costumes[0]
        self.rect = self.costume.get_rect()
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    # This method usually moves a sprite. It will be overwritten here.
    def move(self):
        self.x += self.vx
        self.y += self.vy

    # This method displays the sprite in the stage.
    def display(self, stage, step):
        self.rect.center = ((self.x + 1) * step, (self.y + 1) * step)
        stage.blit(self.costume, self.rect)

    # Since the sprites move on a grid, collision is coordinate based.
    def collides(self, other):
        return (self.x == other.x and self.y == other.y)

"""
    Segments are the parts of the tail of a snake.
    A segment is a sprite with a single costume. It has no other attribute.
"""
class Segment(Sprite):
    def __init__(self, scale, x, y, color):
        Sprite.__init__(self, scale, ["segment_{}".format(color)], x, y)
    # A segment moves in a special way,
    # to the coordinates of another segment (or the head).
    def move(self, other):
        self.x = other.x
        self.y = other.y

"""
    A head the front part of a snake. is another sprite with a single costume. It has a special moving method; a string parameter decides its direction.
"""
class Head(Sprite):
    def __init__(self, scale, x, y, max_x, max_y, color):
        Sprite.__init__(self, scale, ["head_{}".format(color)], x, y, scale)
        self.max_x = max_x
        self.max_y = max_y

    def move(self, direction):
        if direction == "down":
            self.y += 1
            if self.y == self.max_y:
                self.y = 0
        elif direction == "up":
            self.y -= 1
            if self.y == -1:
                self.y = self.max_y - 1
        elif direction == "right":
            self.x += 1
            if self.x == self.max_x:
                self.x = 0
        elif direction == "left":
            self.x -= 1
            if self.x == -1:
                self.x = self.max_x - 1

"""
    A snake is a complex object consisting of a head, a tail that is a list of its body sections, and a few other attributes. Its direction will determine the movement of the head; and the tail will follow the head. It cannot turn in opposite direction.
"""
class Snake():
    def __init__(self, scale, direction, x, y, max_x, max_y, key_map, color):
        self.scale = scale
        self.color = color
        self.head = Head(scale, x, y, max_x, max_y, color)
        self.opposites = {"right":"left", "left":"right",
                            "up":"down", "down":"up"}
        self.init_direction = direction
        self.init_x = x
        self.init_y = y
        self.key_map = key_map
        self.eat_sound = pg.mixer.Sound("eat.wav")
        self.reset()

    # At reset, a snake is put back to its initial position.
    # Its tail is cut back, and it uses all its points.
    # Its keybuffer is emptied, too, to avoid unintended turns.
    def reset(self):
        self.direction = self.init_direction
        self.head.x = self.init_x
        self.head.y = self.init_y
        self.tail = []
        self.grow(2)
        self.score = 0
        self.key_buffer = []
        # The head is moved to avoid collision after reset.
        self.head.move(self.direction)

    # This method displays the head and the segments.
    def display(self, stage, step):
        for segment in self.tail:
            segment.display(stage, step)
        self.head.display(stage, step)

    # The head moves in the direction of the snake.
    # All segments replace the ones ahead of them.
    def move(self):
        if self.key_buffer != []:
            new_dir = self.key_buffer.pop(0)
            self.turn(self.key_map[new_dir])
        for i in range(0, len(self.tail)-1):
            segment = self.tail[i]
            segment_ahead = self.tail[i+1]
            segment.move(segment_ahead)
        self.tail[-1].move(self.head)
        self.head.move(self.direction)

    # This method is called at keydown events.
    # The snake doesn't turn to a direction opposite to its current one.
    def turn(self, new_direction):
        if not new_direction == self.opposites[self.direction]:
            self.direction = new_direction

    # When the snake grows, its tail gets appended by new segments.
    # New segments are all at the same place at first,
    # and then they move one by one.
    # Thus it looks like as if they were added one by one.
    def grow (self, length):
        if self.tail == []:
            last = self.head
        else:
            last = self.tail[0]
            self.score += length
        new_tail = [Segment(self.scale, last.x, last.y, self.color) for _ in range(length)]
        self.tail = new_tail + self.tail

    # This method checks if the head collides with the tail of a snake
    # or a maze cell. Returns True or False.
    def collides(self, snakes, maze):
        to_check = [x for s in snakes for x in s.tail] + maze.cells
        return max(map(self.head.collides, to_check))

    # If the head collides with a donut,
    # the snake grows and the donut is reset.
    # The more the donut's value, the more the snake grows.
    def eat_if_you_can(self, donuts):
        for donut in donuts:
            if self.head.x == donut.x and self.head.y == donut.y:
                self.grow(donut.value)
                donut.to_be_reset = True
                self.eat_sound.play()

# A maze cell is an unmovable piece of sprite.
class MazeCell(Sprite):
    def __init__(self, scale, x, y):
        Sprite.__init__(self, scale, ["mazecell"], x, y)

# A maze is a list of maze cells. The cells are read from files.
class Maze():
    def __init__(self, scale, level):
        self.cells = []
        with open("maze{}.txt".format(level)) as f:
            rows = f.read().split("\n")
        for y, row in enumerate(rows):
            for x, cell in enumerate(row):
                if cell == "#":
                    self.cells += [MazeCell(scale, x, y)]

    def display(self, stage, step):
        for cell in self.cells:
            cell.display(stage, step)

# A donut is a very simple sprite.
class Donut(Sprite):
    def __init__(self, scale, lifetime):
        Sprite.__init__(self, scale, ["donut1", "donut2", "donut3"], 0, 0)
        self.lifetime = lifetime
        self.to_be_reset = True

    def reset(self):
        costume_index = r.randrange(3)
        self.costume = self.costumes[costume_index]
        self.value = 6 + costume_index * 3
        self.age = 0
        self.to_be_reset = False

    # The life cycle of a donut is measured by its age attribute.
    # Once it reaches the donut's lifetime, the donut is reset.
    def move(self):
        self.age += 1
        if self.age == self.lifetime:
            self.to_be_reset = True

class Menu():
    def __init__(self, stage, items, color, bg_color, font_size):
        self.stage = stage
        self.items = items
        self.length = len(self.items)
        self.hcolor = self.colorize(color, 20)
        self.color = self.colorize(color, -20)
        self.bg_color = bg_color
        self.font = pg.font.SysFont(pg.font.get_default_font(), font_size)
        self.hfont = pg.font.SysFont(pg.font.get_default_font(), int(font_size*1.2))
        self.highlighted = 0
        size_x, size_y = pg.display.get_window_size()
        y_dist = size_y // (len(self.items) + 1)
        self.positions = [(size_x//2, int(y_dist*(i+1))) for i in range(self.length)]
        self.done = False

    def colorize(self, color, diff):
        def diff_value(colorvalue):
            dv = colorvalue + diff
            if dv < 0: return 0
            elif 255 < dv: return 255
            else: return dv
        return tuple(map(diff_value, color))

    def refresh_screen(self):
        self.stage.fill(self.bg_color)
        for i, x in enumerate(self.items):
            if i == self.highlighted:
                text = self.hfont.render(self.items[i], False, self.hcolor)
                rect = text.get_rect()
                rect.center = self.positions[i]
                self.stage.blit(text, rect)
                self.frame(rect)
            else:
                text = self.font.render(self.items[i], False, self.color)
                rect = text.get_rect()
                rect.center = self.positions[i]
                self.stage.blit(text, rect)
        pg.display.flip()

    def frame(self, rect):
        frame_rect = rect.inflate(18, 18)
        pg.draw.rect(self.stage, self.color, frame_rect, width = 3, border_radius=5)

    def check_keys(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                sys.exit()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    sys.exit()
                elif event.key in [pg.K_UP, pg.K_w]:
                    self.highlighted = (self.highlighted - 1) % self.length
                elif event.key in [pg.K_DOWN, pg.K_w]:
                    self.highlighted = (self.highlighted + 1) % self.length
                elif event.key in [pg.K_SPACE, pg.K_RETURN]:
                    self.done = True

    def menu(self):
        while not self.done:
            self.refresh_screen()
            self.check_keys()
        pg.time.delay(100)
        return self.highlighted

class Snake_Game():
    def __init__(self, scale, players, levels):
        # Pygame is initialized.
        pg.init()
        pg.mixer.init()
        self.scale = scale
        self.players = players
        self.last_level = levels
        self.level = 0
         # mazes are sized 31*23
         # if you change these values, you have to redesign the mazes
        self.size_x = 31
        self.size_y = 23
        # images are 30*30 pixels
        # if you change this value, you have to change the image files
        self.step = 30 * scale
        # stage size is 960 * 720
        # window size may differ from this due to scaling
        self.stage_x = (int((self.size_x + 1) * self.step))
        self.stage_y = (int((self.size_y + 1) * self.step))
        self.mid_x = self.size_x // 2
        self.mid_y = self.size_y // 2
        self.stage = pg.display.set_mode((self.stage_x, self.stage_y))
        pg.display.set_caption("Snake Game")
        self.bg_color = (20,20,50)
        self.font_color = (210, 210, 40)
        self.font_size = int(60 * scale)
        tfont_size = int(120 * scale)
        self.font = pg.font.SysFont(pg.font.get_default_font(), self.font_size)
        self.titlefont = pg.font.SysFont(pg.font.get_default_font(), tfont_size)
        self.clock = pg.time.Clock()
        self.fps = 5
        self.paused = False
        self.load_sounds()

    def load_sounds(self):
        self.ticksound = pg.mixer.Sound("tick.wav")
        self.levelsound = pg.mixer.Sound("level.wav")
        self.menusound = pg.mixer.Sound("level.wav")
        self.introsound = pg.mixer.Sound("intro.wav")
        self.collidesound = pg.mixer.Sound("collide.wav")

# font = pg.font.SysFont(pg.font.get_default_font(), 60)
# stage.blit(font.render(str(score), False, "white"), (0,0))
    def create_sprites(self):
        self.maze = None
        self.snakes = self.create_snakes()
        self.donuts = self.create_donuts()
        self.sprites = self.snakes + self.donuts

    def create_snakes(self):
        key_map1 = {pg.K_UP: "up", pg.K_DOWN: "down",
                    pg.K_RIGHT: "right", pg.K_LEFT: "left"}
        key_map2 = {pg.K_w: "up", pg.K_s: "down",
                    pg.K_d: "right", pg.K_a: "left"}
        if self.players == 1:
            snake = Snake(scale=self.scale, direction="right",
                        x=self.mid_x, y=self.mid_y,
                        max_x=self.size_x, max_y=self.size_y,
                        key_map={**key_map1,**key_map2}, color="blue")
            return [snake]
        else:
            snake1 = Snake(scale=self.scale, direction="right",
                        x=self.mid_x+1, y=self.mid_y,
                        max_x=self.size_x, max_y=self.size_y,
                        key_map=key_map1, color="blue")
            snake2 = Snake(scale=self.scale, direction="left",
                        x=self.mid_x-1, y=self.mid_y,
                        max_x=self.size_x, max_y=self.size_y,
                        key_map=key_map2, color="red")
            return [snake1, snake2]

    def create_donuts(self):
        def donut():
            return Donut(scale=self.scale, lifetime=self.fps*9)
        donuts = [donut() for _ in range(self.players)]
        return donuts

    def reset_donut(self, donut):
        def on_maze(donut):
            forbidden = [x for x in self.maze.cells]
            return max([donut.collides(x) for x in forbidden])

        def on_snake(donut):
            forbidden = [x for s in self.snakes for x in s.tail + [s.head]]
            return max([donut.collides(x) for x in forbidden])
        donut.reset()
        donut.x = self.snakes[0].head.x
        donut.y = self.snakes[0].head.y
        while on_snake(donut) or on_maze(donut):
            donut.x = r.randrange(self.size_x)
            donut.y = r.randrange(self.size_y)

    def next_level(self):
        self.level += 1
        self.score = 0
        self.maze = Maze(self.scale, self.level)
        for snake in self.snakes:
            snake.reset()
        for donut in self.donuts:
            self.reset_donut(donut)
        self.firstFrame = True

    # Event handling:
    # - ESC quits
    # - P pauses
    # - keys in the snake's keymap control the snake
    def check_keys(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                sys.exit()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    sys.exit()
                elif event.key == pg.K_p:
                    self.paused = not self.paused
                else:
                    for snake in self.snakes:
                        if event.key in snake.key_map:
                            snake.key_buffer.append(event.key)

    def check_donuts(self):
        for donut in self.donuts:
            if donut.to_be_reset:
                self.reset_donut(donut)

    # The snake moves, the donut keeps waiting or jumps.
    def move_sprites(self):
        for sprite in self.sprites:
            sprite.move()

    def display_text(self, text, pos, align="C", title=False):
        if title:
            text_rendered = self.titlefont.render(text, False, self.font_color)
        else:
            text_rendered = self.font.render(text, False, self.font_color)
        text_rect = text_rendered.get_rect()
        display_pos = ((pos[0] + 1) * self.step, (pos[1] + 1) * self.step)
        if align == "L":
            text_rect.midleft = display_pos
        elif align == "R":
            text_rect.midright = display_pos
        else:
            text_rect.center = display_pos
        self.stage.blit(text_rendered, text_rect)

    def handle_score_and_level(self):
        self.score = sum([s.score for s in self.snakes])
        score_text = "Score: {} / {}".format(self.score, self.score_limit)
        score_pos = (1, 1)
        self.display_text(score_text, score_pos, "L")
        level_text = "Level: {}".format(self.level)
        level_pos = (30, 1)
        self.display_text(level_text, level_pos, "R")

    # The stage is refreshed with the score and the sprites.
    def refresh_stage(self):
        self.stage.fill(self.bg_color)
        self.maze.display(self.stage, self.step)
        for sprite in self.sprites:
            sprite.display(self.stage, self.step)
        self.handle_score_and_level()
        pg.display.flip()

    # Intro: The title is displayed. The game starts in 2 seconds.
    def intro(self):
        self.introsound.play()
        self.stage.fill(self.bg_color)
        title = "Snake Game"
        title_pos = (self.mid_x, self.mid_y - 2)
        self.display_text(title, title_pos, align="C", title=True)
        controls = "Control: WASD or arrow keys"
        controls_pos = (self.mid_x, self.size_y - 6)
        self.display_text(controls, controls_pos)
        pause = "Pause: P"
        pause_pos = (self.mid_x, self.size_y - 4)
        self.display_text(pause, pause_pos)
        pg.display.flip()
        self.clock.tick(self.fps / 10)

    # Outro: The endtitle is displayed (without erasing the stage).
    # The new lwvwl begins in one second, or the game is closed in 2 seconds.
    def level_outro(self):
        # self.save_highscore()
        self.levelsound.play()
        if self.level < self.last_level:
            endtitle = "Level {} done! :)".format(self.level)
            end_fps = self.fps / 5
        else:
            endtitle = "You made it! :)"
            end_fps = self.fps / 10
        endtitle_pos = (self.mid_x, self.mid_y)
        self.display_text(endtitle, endtitle_pos, align="C", title=True)
        pg.display.flip()
        self.clock.tick(end_fps)

    def pause_display(self):
        paused = "Game paused"
        paused_pos = (self.mid_x, self.mid_y - 2)
        self.display_text(paused, paused_pos, align="C", title=True)
        unpause = "P to continue"
        unpause_pos = (self.mid_x, self.size_y - 6)
        self.display_text(unpause, unpause_pos)
        pg.display.flip()

    def check_collisions(self):
        for snake in self.snakes:
            snake.eat_if_you_can(self.donuts)
            if snake.collides(self.snakes, self.maze):
                self.collidesound.play()
                snake.reset()

    def players_menu(self):
        menu_items = ["One player", "Two players"]
        menu = Menu(self.stage, menu_items, self.font_color, self.bg_color, self.font_size)
        selection = menu.menu()
        self.menusound.play()
        self.players = selection + 1

    def difficulty_menu(self):
        menu_items = ["Easy", "Medium", "Hard"]
        menu = Menu(self.stage, menu_items, self.font_color, self.bg_color, self.font_size)
        selection = menu.menu()
        self.menusound.play()
        self.score_limit = (selection + 1) * 60

    def tick(self):
        if self.firstFrame:
            self.clock.tick(self.fps / 5)
            self.firstFrame = False
        else:
            self.ticksound.play()
            self.clock.tick(self.fps)

    # This is the main loop of the game.
    # The details of implementation are hidden from here.
    # The game ends when the snake self-collides.
    def play(self):
        self.intro()
        self.players_menu()
        self.difficulty_menu()
        self.create_sprites()
        while self.level < self.last_level:
            self.next_level()
            while self.score < self.score_limit:
                self.check_keys()
                if self.paused:
                    self.pause_display()
                else:
                    self.move_sprites()
                    self.check_collisions()
                    self.check_donuts()
                    self.refresh_stage()
                    self.tick()
            self.level_outro()

if __name__ == "__main__":
    # scale = 0.5: 480*360 game window
    # scale = 1: : 960*720 game window
    game = Snake_Game(scale=0.8, players=2, levels=5)
    game.play()
