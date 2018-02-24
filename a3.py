"""
CSSE1001 Assignment 3
Semester 2, 2017
"""

# There are a number of jesting comments in the support code
# They should not be taken seriously. Keep it fun folks :D
# Students are welcome to add their own source code humour, provided it remains civil

import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.messagebox import showinfo
from tkinter import messagebox
import os
import random
import pyglet
import pygame as pg
import fileinput
import sys

try:
    from PIL import ImageTk, Image

    HAS_PIL = True
except ImportError:
    print('k')
    HAS_PIL = False

from view import GridView, ObjectivesView
from game import DotGame, ObjectiveManager, CompanionGame
from dot import BasicDot, AbstractDot, WildcardDot
from util import create_animation, ImageManager
from companion import AbstractCompanion, UselessCompanion
from cell import Cell, VoidCell

# Fill these in with your details
__author__ = "Quoc Trung Cao (s4459239)"
__email__ = "q.cao@uq.net.au"
__date__ = "27 Oct 2017"

__version__ = "1.1.1"


def load_image_pil(image_id, size, prefix, suffix='.png'):
    """Returns a tkinter photo image

    Parameters:
        image_id (str): The filename identifier of the image
        size (tuple<int, int>): The size of the image to load
        prefix (str): The prefix to prepend to the filepath (i.e. root directory
        suffix (str): The suffix to append to the filepath (i.e. file extension)
    """
    width, height = size
    file_path = os.path.join(prefix, f"{width}x{height}", image_id + suffix)
    return ImageTk.PhotoImage(Image.open(file_path))


def load_image_tk(image_id, size, prefix, suffix='.gif'):
    """Returns a tkinter photo image

    Parameters:
        image_id (str): The filename identifier of the image
        size (tuple<int, int>): The size of the image to load
        prefix (str): The prefix to prepend to the filepath (i.e. root directory
        suffix (str): The suffix to append to the filepath (i.e. file extension)
    """
    width, height = size
    file_path = os.path.join(prefix, f"{width}x{height}", image_id + suffix)
    return tk.PhotoImage(file=file_path)

def play_theme_song(song, mode, suffix='.mp3'):
    """Plays a loaded .mp3 or .wav file without interupting the program.

    Parameters:
        song (str): The filename of the song located in the same directory

    Returns:
        None.
    """
    pg.mixer.init()
    pg.mixer.music.load(r'''{}\\sounds\\{}{}'''.format(os.getcwd(),song,suffix))
    if mode == 1:
        pg.mixer.music.play(-1)
    elif mode == 2:
        pg.mixer.music.rewind()
    else:
        pg.mixer.music.stop()


# This allows you to simply load png images with PIL if you have it,
# otherwise will default to gifs through tkinter directly
load_image = load_image_pil if HAS_PIL else load_image_tk  # pylint: disable=invalid-name

DEFAULT_ANIMATION_DELAY = 0  # (ms)
ANIMATION_DELAYS = {
    # step_name => delay (ms)
    'ACTIVATE_ALL': 50,
    'ACTIVATE': 100,
    'ANIMATION_BEGIN': 300,
    'ANIMATION_DONE': 0,
    'ANIMATION_STEP': 200
}

NO_COMPANION = 1
COMPANION = 2


# Define your classes here
# You may edit as much of DotsApp as you wish
class Manager(Tk):
    """ Main window that handles all children frames. """
    
    def __init__(self,*args,**kwargs):
        Tk.__init__(self,*args,**kwargs)
        container = Frame(self)
        container.grid()
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0,weight=1)
        self.frames = {}
        self.title('Dots & Co')
        self.iconbitmap(r'{}\\images\\fireball.ico'.format(os.getcwd()))
        for F in (LogIn, PreGame):
            frame = F(container,self)
            self.frames[F] = frame
            frame.grid(row=0,column=0,sticky="nsew")
        self.show_Window(LogIn)
        self.protocol('WM_DELETE_WINDOW', self.ask)

    def show_Window(self,cont):
        frame = self.frames[cont]
        frame.tkraise()
        Tk.update(self)

    def ask(self):
        ans = messagebox.askyesno('Exiting Dots&Co','Are you sure you want to quit?')
        if ans:
            self.destroy()
        else:
            return
  
    
class LogIn(Frame):
    """ Log in window."""

    checkpoint = 1
    player = 'None'
    
    def __init__(self, master, controller):
        Frame.__init__(self, master)
        self._accounts = {}
        
        self._master = master
        
        self._status = ''
        self._controller = controller
        
        background = Image.open(r'{}\\images\\dots_co.jpg'.format(os.getcwd()))
        background.thumbnail((900,320))
        photo_image = ImageTk.PhotoImage(background)
        self._login_backgrnd = ttk.Label(self, image = photo_image)
        self._login_backgrnd.image = photo_image
        self._login_backgrnd.grid(row=0,column=0,columnspan=4)
        
        self._label_1 = ttk.Label(self,text='Username').grid(row=1,column=0,columnspan=1)
        self._label_2 = ttk.Label(self,text='Password').grid(row=2,column=0,columnspan=1,pady=3)

        self._input_1 = Entry(self)
        self._input_1.grid(row=1,column=1,columnspan=3,ipadx=88)
        
        self._input_2 = Entry(self,show='*')
        self._input_2.grid(row=2,column=1,columnspan=3,ipadx=88,pady=3)

        self._sign_up_btn = tk.Button(self,text='Sign Up',bg='light coral',\
                                       command=self.sign_up)
        self._sign_up_btn.grid(row=3,column=0,columnspan=1,ipadx=21,ipady=15)

        self._sign_in_btn = tk.Button(self,text='Sign In',bg='light salmon',\
                                       command=self.sign_in)
        self._sign_in_btn.grid(row=3,column=1,columnspan=1,ipadx=25,ipady=15)

        self._refresh_btn = tk.Button(self,text='Refresh',bg='tomato',\
                                       command=self.refresh)
        self._refresh_btn.grid(row=3,column=2,columnspan=1,ipadx=22,ipady=15)

        self._quit_btn = tk.Button(self,text='Quit',bg='coral',\
                                    command=self.quit)
        self._quit_btn.grid(row=3,column=3,columnspan=1,ipadx=30,ipady=15)

        try:
            with open('player_data.txt','r') as f:
                for line in f:
                    u, p, s, r = line.split(' ')
                    r = r.strip('\n')
                    self._accounts[u] = (p,s,r)       
        except Exception:
            self._status = 'file not exist'        
        self._mode = 'unsigned in'    

    def sign_up(self):
        """Creates and saves new account in text file."""
        self.sound()
        username = self._input_1.get()
        password = self._input_2.get()
        score = 0
        if username in self._accounts:
            messagebox.showinfo('Username is already taken','Please choose another username')
        else:
            with open('player_data.txt','a') as f:
                f.writelines('{} {} {} 1\n'.format(username, password, score))
            messagebox.showwarning('Sign up successfull','Press refresh and login')
               
    def sign_in(self):
        """Reads and verifies logging into an account."""
        self.sound()
        username = self._input_1.get()
        password = self._input_2.get()
        if self._status == 'file not exist':
            messagebox.showwarning('Login failed','Username does not exist')

        try:
            if self._status == '' and self._accounts[username][0] == password:
                self._mode = 'logged in'
                self.set_checkpoint(int(self._accounts[username][2]))
                self.set_player(username)
                self._controller.show_Window(PreGame)
                self._login_backgrnd.destroy()
            elif self._status == '' and username == '':
                messagebox.showwarning('Login failed','Username cannot be blank')
                self._input_1.delete(0, END)
                self._input_2.delete(0, END)
            else:
                messagebox.showwarning('Login failed','Incorrect password')
                self._input_2.delete(0, END)
        except KeyError:
            messagebox.showwarning('Login failed','Username does not exist')
            self._input_1.delete(0, END)
            self._input_2.delete(0, END)

    def quit(self):
        """Destroys tkinter window."""
        ans = messagebox.askokcancel('Exitting Dots&Co','Are you sure you want to quit?')
        if ans:
            self._controller.destroy()
        else:
            return

    def get_mode(self):
        """Returns app mode as a string."""
        return self._mode

    def refresh(self):
        """Refresh account storage text file."""
        
        try:
            with open('player_data.txt','r') as p:
                for line in p:
                    u, p, s, r = line.split(' ')
                    r = r.strip('\n')
                    self._accounts[u] = (p,s,r)
                    self._status = ''          
        except Exception:
            self._status = 'file not exist'

    def sound(self):
        """Plays a sound after click."""
        sound = pyglet.media.load(r'{}\\sounds\\cash_sound.wav'.format(os.getcwd()))
        sound.play()

    @classmethod
    def set_checkpoint(cls, checkpoint):
        """Sets the game checkpoint."""
        cls.checkpoint = checkpoint

    @classmethod
    def set_player(cls, player):
        """Sets player's username."""
        cls.player = player
        
    @classmethod
    def get_checkpoint(cls):
        """Returns the game's checkpoint as an integer."""
        return LogIn.checkpoint

    @classmethod
    def get_player(cls):
        """Returns player's username as a string."""
        return LogIn.player


class PreGame(LogIn):
    """ Pre-game window for companion and game mode selection."""
    
    def __init__(self, parrent, controller, **kwargs):
        LogIn.__init__(self, parrent, controller)
        for widget in self.winfo_children():
            widget.destroy()

        self._controller = controller
        self._controller.geometry('395x425')

        self._companion = None

        self._checkpoint = LogIn.get_checkpoint()
        self._player = 'None'
        
        self.prompt = Label(self,\
                      text='WELCOME TO DOTS&CO!!\nPlease select your companion!',\
                      font=('Comic Sans MS',15,'bold italic'),compound=tk.CENTER,\
                      foreground='salmon')
        self.prompt.grid(row=0,column=0,columnspan=4,pady=25)

        self._img_buttons = []
        options = ['aristotle','eskimo','captain','buffalo','penguin','goat','deer','useless']

        for i in range(0,len(options)):
            img = Image.open(r'''{0}\\images\\companions\\{1}.png'''.format(\
                          os.getcwd(),options[i]))
            img.thumbnail((70,70))
            self._img_buttons.append(ImageTk.PhotoImage(img))


        self.aristotle = tk.Button(self,height=120,width=95,\
                            command=lambda:self.lock('Aristotle',0))
        self.aristotle.grid(row=1,column=0,pady=5)

        self.eskimo = tk.Button(self,text='Eskimo',height=120,width=95,\
                                command=lambda:self.lock('Eskimo',1))
        self.eskimo.grid(row=1,column=1,pady=5)

        self.captain = tk.Button(self,text='Captain',height=120,width=95,\
                                 command=lambda:self.lock('Captain',2))
        self.captain.grid(row=1,column=2,pady=5)

        self.buffalo = tk.Button(self,text='Buffalo',height=120,width=95,\
                                 command=lambda:self.lock('Buffalo',3))
        self.buffalo.grid(row=1,column=3,pady=5)

        self.penguin = tk.Button(self,text='Penguin',height=120,width=95,\
                                 command=lambda:self.lock('Penguin',4))
        self.penguin.grid(row=2,column=0,pady=5)

        self.goat = tk.Button(self,text='Goat',height=120,width=95,\
                              command=lambda:self.lock('Goat',5))
        self.goat.grid(row=2,column=1,pady=5)

        self.deer = tk.Button(self,text='Deer',height=120,width=95,\
                              command=lambda:self.lock('Deer',6))
        self.deer.grid(row=2,column=2,pady=5)

        self.none = tk.Button(self,text='None',height=120,width=95,\
                              command=lambda:self.lock('Useless',7))
        self.none.grid(row=2,column=3,pady=5)

        self.buttons = [self.aristotle,self.eskimo,self.captain,self.buffalo,self.penguin,self.goat,self.deer,self.none]

        for idx, button in enumerate(self.buttons,0):
            button.config(image=self._img_buttons[idx])
            button.image = self._img_buttons[idx]

        self._origin = self.aristotle.cget('background')

        self.start_button = ttk.Button(self,text='Start New',command=lambda:self.play())
        self.start_button.grid(row=3,column=0,columnspan=1,pady=10)

        self.cont_button = ttk.Button(self,text='Continue Campaign',command=lambda:self.play(cont=True))
        self.cont_button.grid(row=3,column=1,columnspan=2,pady=10)
        
        self.quit_button = ttk.Button(self,text='Quit',command=self.quit)
        self.quit_button.grid(row=3,column=3,columnspan=1,pady=10)

    def lock(self, mode, button):
        self.sound()
        self._companion = mode
        for b in self.buttons:
            b.config(bg=self._origin)
        self.buttons[button].config(bg='Pale Turquoise')

    def play(self, cont = False):
        """Initializes the game in 2 modes.

        Parameters:
            cont (bool): loads previous checkpoint if True, start new otherwise.
        """
        try:
            if self._companion is None:
                raise AttributeError
            else:
                self._player = LogIn.get_player()
                if cont:
                    self._checkpoint = LogIn.get_checkpoint()
                else:
                    self._checkpoint = 1
                self.sound()
                self.grid_forget()
                game = DotsApp(self._controller,self.get_companion(), self._checkpoint,\
                               self._player)
                self._controller.title('Dots&Co')
                self._controller.geometry('990x710')
                self._controller.mainloop()
        except AttributeError:
            ans = messagebox.showwarning('Warning','Please pick a companion mode')

    def get_companion(self):
        """Returns the companion mode as a string."""
        return self._companion

    def sound(self):
        """Plays background sound when a button's pressed."""
        sound = pyglet.media.load(r'{}\\sounds\\cash_sound.wav'.format(os.getcwd()))
        sound.play()

           
class DotsApp:
    """Top level GUI class for simple Dots & Co game"""

    def __init__(self, master, companion_mode, checkpoint, player):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget
        """
            
        self._master = master
        for widget in self._master.winfo_children():
            widget.destroy()

        self._playing = True

        self._image_manager = ImageManager('images/dots/', loader=load_image)

        self._mode = COMPANION

        self._companion_mode = companion_mode
        self._checkpoint = int(checkpoint)
        self._player = player
        print(self._player)
        self._next_round = True
        self.play_theme()

        # Objectives
        self._objectives, self._kinds = self.set_objectives()
    
        # Companion
        if self._companion_mode == 'Aristotle':
            self._companion = AristotleCompanion()
        elif self._companion_mode == 'Eskimo':
            self._companion = EskimoCompanion()
        elif self._companion_mode == 'Captain':
            self._companion = CaptainCompanion()
        elif self._companion_mode == 'Buffalo':
            self._companion = BuffaloCompanion()
        elif self._companion_mode == 'Penguin':
            self._companion = PenguinCompanion()
        elif self._companion_mode == 'Goat':
            self._companion = GoatCompanion()
        elif self._companion_mode == 'Deer':
            self._companion = DeerCompanion()
        elif self._companion_mode == 'Useless':
            self._mode = NO_COMPANION
            self._companion = UselessCompanion()

        self._dead_cells ={(1, 1), (6, 1), (1, 6), (6, 6)}

        # Game
        if self._mode == COMPANION:
            self._game = CompanionGame({CompanionDot:0.2,BasicDot: 0.8}, companion=self._companion, objectives=self._objectives, kinds=self._kinds, size=(8, 8),
                             dead_cells=self._dead_cells)
        else:
            self._game = DotGame({BasicDot: 1}, objectives=self._objectives, kinds=self._kinds, size=(8, 8),
                             dead_cells=self._dead_cells)

        # Info panel
        self._info_panel = InfoPanel(master, self)
        self._info_panel.grid(row=0,column=0,columnspan=2)
        self._turn = self._game.get_moves()
        if self._mode == COMPANION:
            self._info_panel.turn_update(self._turn, self._game.get_score(),
                self._companion.get_charge(), self._objectives, self._checkpoint)
        else:
            self._info_panel.turn_update(self._turn, self._game.get_score(),
                                     0, self._objectives, self._checkpoint)
            
        # Campaign bar
        self._campaign = CampaignBar(master, self._info_panel, 1)
        self._campaign.grid(row=2,column=0,columnspan=2)
        
        # Update round
        self.update_round()
        
        # Grid View
        self._grid_view = GridView(master, size=self._game.grid.size(), image_manager=self._image_manager)
        self._grid_view.grid(row=3,column=0,columnspan=2)
        self._grid_view.draw(self._game.grid)
        self.draw_grid_borders()

        # Events
        self.bind_events()

        # Set initial score again to trigger view update automatically
        self._refresh_status()
        
        # Interval bar
        self._progress_bar = IntervalBar(master, self._info_panel)
        self._progress_bar.grid(row=1,column=0,columnspan=2)
        self._progress_bar.set_step(0)
        self._progress_bar.update_bar()

        # File Menu and Dialogs
        menubar = tk.Menu(self._master)
        self._master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label='File',menu=filemenu)
        filemenu.add_command(label='New Game',command=self.new_game)
        filemenu.add_command(label='Restart',command=self.reset)
        filemenu.add_command(label='Load Previous',command=self.load_previous)
        filemenu.add_command(label='Save Game',command=self.save)
        filemenu.add_command(label='Exit',command=self.exit)
          
    def get_dead_cells(self):
        """Return all dead cells on the grid as a set"""
        return self._dead_cells

    def draw_grid_borders(self):
        """Draws borders around the game grid"""
        borders = list(self._game.grid.get_borders())

        # this is a hack that won't work well for multiple separate clusters
        outside = max(borders, key=lambda border: len(set(border)))

        for border in borders:
            self._grid_view.draw_border(border, fill=border != outside)

    def reset_borders(self):
        """Clears the current grid borders for redrawing."""
        self._grid_view.destroy()
        self._grid_view = GridView(self._master, size=self._game.grid.size(), image_manager=self._image_manager)
        self._grid_view.grid(row=3,column=0,columnspan=2)
        self._grid_view.draw(self._game.grid)
        self.draw_grid_borders()

    def bind_events(self):
        """Binds relevant events"""
        self._grid_view.on('start_connection', self._drag)
        self._grid_view.on('move_connection', self._drag)
        self._grid_view.on('end_connection', self._drop)
        self.bind_game_events()

    def bind_game_events(self):
        """Binds relevant events to the current game"""
        self._game.on('reset', self._refresh_status)
        self._game.on('complete', self._drop_complete)
        self._game.on('connect', self._connect)
        self._game.on('undo', self._undo)

    def unbind_all(self):
        """Unbinds all events of the current game to start a new branch"""
        self._game.off_all()

    def _animation_step(self, step_name):
        """Runs for each step of an animation
        
        Parameters:
            step_name (str): The name (type) of the step    
        """
        print(step_name)
        self._refresh_status()
        self.draw_grid()

    def animate(self, steps, callback=lambda: None):
        """Animates some steps (i.e. from selecting some dots, activating companion, etc.
        
        Parameters:
            steps (generator): Generator which yields step_name (str) for each step in the animation
        """
        if steps is None:
            steps = (None for _ in range(1))

        animation = create_animation(self._master, steps,
                                     delays=ANIMATION_DELAYS, delay=DEFAULT_ANIMATION_DELAY,
                                     step=self._animation_step, callback=callback)
        animation()

    def _drop(self, position):  # pylint: disable=unused-argument
        """Handles the dropping of the dragged connection

        Parameters:
            position (tuple<int, int>): The position where the connection was
                                        dropped
        """
        if not self._playing:
            return

        if self._game.is_resolving():
            return

        self._grid_view.clear_dragged_connections()
        self._grid_view.clear_connections()

        self.animate(self._game.drop())

    def _connect(self, start, end):
        """Draws a connection from the start point to the end point

        Parameters:
            start (tuple<int, int>): The position of the starting dot
            end (tuple<int, int>): The position of the ending dot
        """
        if self._game.is_resolving():
            return
        if not self._playing:
            return
        self._grid_view.draw_connection(start, end,
                                        self._game.grid[start].get_dot().get_kind())

    def _undo(self, positions):
        """Removes all the given dot connections from the grid view

        Parameters:
            positions (list<tuple<int, int>>): The dot connects to remove
        """
        for _ in positions:
            self._grid_view.undo_connection()

    def _drag(self, position):
        """Attempts to connect to the given position, otherwise draws a dragged
        line from the start

        Parameters:
            position (tuple<int, int>): The position to drag to
        """
        if self._game.is_resolving():
            return
        if not self._playing:
            return

        tile_position = self._grid_view.xy_to_rc(position)

        if tile_position is not None:
            cell = self._game.grid[tile_position]
            dot = cell.get_dot()

            if dot and self._game.connect(tile_position):
                self._grid_view.clear_dragged_connections()
                return

        kind = self._game.get_connection_kind()

        if not len(self._game.get_connection_path()):
            return

        start = self._game.get_connection_path()[-1]

        if start:
            self._grid_view.draw_dragged_connection(start, position, kind)

    @staticmethod
    def remove(*_):
        """Deprecated in 1.1.0"""
        raise DeprecationWarning("Deprecated in 1.1.0")

    def draw_grid(self):
        """Draws the grid"""
        self._grid_view.draw(self._game.grid)

    def reset(self, new=False):
        """Resets the game"""
        self._playing = True
        self.unbind_all()

        if new:
            self._objectives, self._kinds = self.set_objectives()

        if self._mode == COMPANION:
            self._game.companion.reset()
            weights = {CompanionDot:0.3, BasicDot: 0.7}
        elif self._mode == NO_COMPANION:
            weights = {BasicDot: 1}

        
        if self._checkpoint == 1:
            self._dead_cells ={(1, 1), (6, 1), (1, 6), (6, 6)}
        elif self._checkpoint == 2 :
            self._dead_cells ={(3, 3), (3, 4), (4, 3), (4, 4)}
        elif self._checkpoint == 3:
            self._dead_cells = set()
        else:
            self._dead_cells ={(0, 0), (0, 7), (7, 0), (7, 7)}
            
        self._game = CompanionGame(weights, companion=self._companion, objectives=self._objectives,
                                kinds=self._kinds, size=(8, 8),
                                dead_cells=self._dead_cells)
        self._objectives.reset()
        self._progress_bar.reset_bar()

        #Refresh and update info panel
        self._info_panel.turn_update(self._game.get_moves(), self._game.get_score(),
                self._companion.get_charge(), self._objectives, self._checkpoint)
        self._game.reset()
        self.update_round()
        self.reset_borders()
        self.bind_game_events()
        self.bind_events()
        self._refresh_status()
             
        #Rewind theme song
        self.play_theme()
   
    def check_game_over(self):
        """Checks whether the game is over and shows an appropriate message box if so"""
        state = self._game.get_game_state()

        if state == self._game.GameState.WON:
            showinfo("Round Over!", "You won {}!!!".format(self._player))
            self._playing = False
            if int(self._checkpoint) < 4:
                self._next_round = True
            else:
                self._next_round = False
                
        elif state == self._game.GameState.LOST:
            showinfo("Round Over!",
                     f"You didn't reach the objective(s) in time. You connected {self._game.get_score()} points")
            self._playing = False
            self._next_round = False

    def _drop_complete(self):
        """Handles the end of a drop animation"""
        self.draw_grid()
        self._drop_snd = pyglet.media.load(r'{}\\sounds\\coin2.wav'.format(os.getcwd()))
        self._drop_snd.play()
        print("GAME MODE: {}".format(self._mode))
        self._info_panel.turn_update(self._game.get_moves(), self._game.get_score(),
                        self._companion.get_charge(), self._objectives, self._checkpoint)
    
        if self._game.get_game_state() == self._game.GameState.PLAYING:
            
            if self._mode == COMPANION:
                self.update_progress()
                if self._game.companion.is_fully_charged():
                    self._game.companion.reset()
                    steps = self._game.companion.activate(self._game, self)
                    return self.animate(steps)
                
            self._refresh_status()
    
        else:
            self.check_game_over()
            if self._next_round and self._checkpoint <4:
                ans = messagebox.askyesno('Round Over!!!','Go to next round?')
                if ans:
                    self._checkpoint += 1
                    self.reset()
                else:
                    return
            
            elif not self._next_round and self._checkpoint == 4 and self._game.get_game_state == self._game.GameState.WON:
                ans = messagebox.askyesno('Congratulations {}!'.format(self._player),\
                                          'Restart campaign?')
                if ans:
                    self.reset()
                else:
                    return
                      
    def _refresh_status(self):
        """Handles change in score"""

        # Normally, this should raise the following error:
        # raise NotImplementedError()
        # But so that the game can work prior to this method being implemented,
        # we'll just print some information
        # Sometimes I believe Python ignores all my comments :(
        score = self._game.get_score()
        print("Score is now {}.".format(score))

    def exit(self):
        """Handles exit method."""
        ans = messagebox.askokcancel('Exitting Dots&Co','Are you sure you want to quit?')
        if ans:
            self._master.destroy()
        else:
            return
        
    def update_progress(self):
        """Updates the interval bar."""
        if self._companion.get_charge() == 6:
            self._progress_bar.reset_bar()
        else:
            self._progress_bar.set_step(self._companion.get_charge())
            self._progress_bar.update_bar()
            
    def get_objectives(self):
        """Returns the objectives of the current game."""
        return self._objectives

    def save(self):
        """Overrides the content of the player in player_data.txt."""
        with open('player_data.txt','r') as f:
            for line in f:
                if line.startswith('{} '.format(self._player)):
                    u,p,s,r = line.strip('\n').split(' ')
                    new_line = '{} {} {} {}\n'.format(u,p,s,self._checkpoint)
            
        self.replace_line('player_data.txt',line,new_line)
        messagebox.showinfo('Game saved','Checkpoint is successfully saved')

    def replace_line(self,file,search,replace):
        """Replaces the content of an identified line in a text file."""
        for line in fileinput.input(file, inplace=1):
            if search in line:
                line = line.replace(search,replace)
            sys.stdout.write(line)

    def load_previous(self):
        """Loads the previously saved checkpoint."""
        to_read = None
        with open('player_data.txt','r') as f:
                for line in f:
                    if line.startswith('{} '.format(self._player)):
                        to_read = line
        print('hey',to_read)
        u, p, s, r = to_read.split(' ')
        r = r.strip('\n')
        self._checkpoint = int(r)
        self.reset()

    def new_game(self):
        """Creates a new game."""
        ans = messagebox.askyesno('Start a new game','Do you want to use companion?')
        if ans:
            self._mode = COMPANION
            self._master.destroy()
            app = Manager()
            app.show_Window(PreGame)
        else:
            self._companion = UselessCompanion()
            self._mode = NO_COMPANION
            self._info_panel.companion_update('useless')
            self.reset(new=True)

    def set_objectives(self):
        """Sets random objectives for the game.

        Parameters:
            None.

        Return:
            tuple(ObjectiveManager, tuple<int>)
        """
        counts = []
        for i in range(0,4):
            counts.append(random.randint(0,10))
        random.shuffle(counts)

        dots, kinds = self.generate_dots()
        objectives = zip(dots, counts)

        return (ObjectiveManager(list(objectives)), kinds)
        
    def generate_dots(self):
        """Generates 4 random types of dot for the game.

        Parameters:
            None.

        Return:
            tuple(list<BasicDot>, tuple<int>): a tuple of generated dots and their kinds.
        """
        all_dots = []  
        gen_dots = []
        kinds = ()
        
        for i in range(1,14):
            all_dots.append(BasicDot(i))

        while len(gen_dots) <4:
            kind = random.randint(0,12)
        
            if all_dots[kind] not in gen_dots:
                gen_dots.append(all_dots[kind])
                kinds += (kind+1,)
            
        return (gen_dots,kinds)
      
    def generate_cells(self, cells, _kind='live'):
        """Generates random cell positions that are available on the grid.

        Parameters:
            cells (int): number of cells to be generated
            
        Return:
            positions (set(tuple<int, int>)): a set of random positions on the grid
        """
        positions = set()
        dead_cells = self.get_dead_cells()
        
        while len(positions) <= cells:
            if _kind == 'live':
                i = random.randint(0,7)
                j = random.randint(0,7)
            elif _kind == 'dead':
                i = random.randint(1,6)
                j = random.randint(1,6)
            if (i,j) not in positions:
                positions.add((i,j))
        return positions.difference(dead_cells)
            
    def get_companion_mode(self):
        """Returns the game current companion as a string."""
        return self._companion_mode

    def get_checkpoint(self):
        """Returns the game current checkpoint (i.e. round) as an integer."""
        return self._checkpoint

    def update_round(self):
        """Updates each round by placing particular dots"""
        if self._checkpoint == 1:
            turtles = list(self.generate_cells(4).difference(self._dead_cells))
            for pos in turtles:
                self._game.grid[pos].set_dot(TurtleDot('turtle',self))
        elif self._checkpoint == 2:
            anchors = list(self.generate_cells(6).difference(self._dead_cells))
            for pos in anchors:
                self._game.grid[pos].set_dot(AnchorDot('anchor'))
        elif self._checkpoint == 3:
            balloons = []
            while len(balloons) <= 5:
                i = random.randint(0,7)
                if (7,i) not in self.get_dead_cells():
                    balloons.append((7,i))
            for pos in balloons:
                 self._game.grid[pos].set_dot(BalloonDot('balloon'))
        else:
            flowers = list(self.generate_cells(6).difference(self._dead_cells))
            kinds = self._kinds
            for pos in flowers:
                self._game.grid[pos].set_dot(FlowerDot(kinds[random.randint(0,3)]))
        self._campaign.update(self._checkpoint)

    def get_dot_kinds(self):
        """Returns all basic dot kinds on the grid as a tuple(<int, int, int, int>)."""
        return self._kinds

    def get_grid(self):
        """Returns all positions if the grid in a list(tuple<int, int>))."""
        grid = []
        for i in range(0,8):
            for j in range(0,8):
                if isinstance(self._game.grid[(i,j)],Cell):
                    grid.append((i,j))          
        return grid

    def play_theme(self):
        """Selects a random theme for the game"""
        songs = ['james_bond','glad_you_came']
        try:
            pg.mixer.music.stop()
            play_theme_song(songs[random.randint(0,1)],1)
        except Exception:
            play_theme_song(songs[random.randint(0,1)],1)     

    
class InfoPanel(ttk.Frame):
    """ Constructor of the info panel for DotsApp. """
    
    def __init__(self, master, parent):
        super().__init__(master)
        self.parent = parent

        self._label = ttk.Label(self, text = '20', font=('Helvetica', 50))
        self._label.grid(row=0, column=0,ipadx=150,padx=0)

        self._round = ttk.Label(self, text = 'Round 1/4', font=('Comic Sans MS', 20,'bold italic'),\
                                foreground='orange')
        self._round.grid(row=1, column=0,ipadx=150,padx=10)

        self._score_label = ttk.Label(self,text ='0',font=('Helvetica',32),foreground='grey')
        self._score_label.grid(row=0,column=0,sticky='E')
        
        self._img_manager = parent._image_manager
        self._obj_view = ObjectivesView(self, image_manager=self._img_manager)
        self._obj_view.grid(row=0,column=2)

        self._companion = parent.get_companion_mode()

        load_img = Image.open(r'''{0}\\images\\companions\\{1}.png'''.format(os.getcwd(),self._companion))
        load_img.thumbnail((100,100))
        photo = ImageTk.PhotoImage(load_img)
        self._img = ttk.Label(self,image=photo)
        self._img.image = photo
        self._img.grid(row=0,column=1,ipadx=150)

    def turn_update(self, turn, score, charge, objectives, checkpoint):
        """Updates the info panel.

        Parameters:
            turn (int): number of turns left.
            score (int): current score of the game.
            charge (int): current companion's charge.
            objectives (ObjectiveManager): resolved objectives.
            checkpoint (int): current game's checkpoint.
        """
        self._label.config(text='{}'.format(turn))
        self._score_label.config(text='{}'.format(score))
        self._round.config(text='Round {}/4'.format(checkpoint))
        self._obj_view.draw(objectives.get_status())

    def companion_update(self, companion):
        """Updates the companion image on the info panel.

        Parameters:
            companion (str): updated companion.
        """
        load_img = Image.open(r'''{0}\\images\\companions\\{1}.png'''.format(os.getcwd(),companion))
        load_img.thumbnail((100,100))
        photo = ImageTk.PhotoImage(load_img)
        self._img.config(image=photo)


class IntervalBar(tk.Canvas):
    """ Constructor of the interval bar that keeps track of the companion's charge."""
    
    def __init__(self, master, parent):
        super().__init__(master)
        self._step = 0
        self._max_step = 6
        self.config(height='20',width='300',bd=1,relief='sunken')
        self.draw_bar()

    def draw_bar(self):
        """Draws the bars on the grid.""" 
        for i in range(0, self._max_step):
            self.create_rectangle(i*(300/self._max_step),0,(i+1)*(300/self._max_step),20,\
                                  fill='',outline='white')

    def set_step(self, step):
        """Sets the progress of interval bar.

        Parameters:
            step (int): number of charge on interval bar
        """
        self._step = step

    def get_step(self):
        """Returns the current charge of interval bar as an integer."""
        return self._step
    
    def update_bar(self):
        """Updates interval bar."""
        self.delete('all')
        for i in range(0, self._step):
            self.create_rectangle(i*(300/self._max_step),0,(i+1)*(300/self._max_step),20,\
                                  fill='DarkOrchid3',outline='white')
    
    def reset_bar(self):
        """Resets interval bar to 0 charge."""
        self.delete('all')
        for i in range(0, self._max_step):
            self.create_rectangle(i*(300/self._max_step),0,(i+1)*(300/self._max_step),20,\
                                  fill='',outline='white')
            self._step = 0
            self.update_bar()


class CampaignBar(tk.Canvas):
    """ Contructor of the campaign bar that keeps track of the game's checkpoint."""
    
    def __init__(self, master, parent, checkpoint):
        super().__init__(master)
        self._checkpoint = checkpoint
        self._rounds = 4
        self.config(height='40',width='600',bd=0.5)
        self.draw(self._checkpoint)

    def draw(self, checkpoint):
        """Draws checkpoints.

        Parameters:
            checkpoint (int): the game checkpoint to update.
        """
        turtle = Image.open(r'''{}\\images\\turtle.png'''.format(os.getcwd()))
        turtle.thumbnail((30,30))

        anchor = Image.open(r'''{}\\images\\anchor.png'''.format(os.getcwd()))
        anchor.thumbnail((30,30))
        
        balloon = Image.open(r'''{}\\images\\balloon.png'''.format(os.getcwd()))
        balloon.thumbnail((30,30))
        
        flower = Image.open(r'''{}\\images\\flower.png'''.format(os.getcwd()))
        flower.thumbnail((30,30))
        
        self._turtle = ImageTk.PhotoImage(turtle)
        self.create_image(25,30, image=self._turtle)

        self._anchor = ImageTk.PhotoImage(anchor)
        self.create_image(215,30, image=self._anchor)

        self._balloon = ImageTk.PhotoImage(balloon)
        self.create_image(400,30, image=self._balloon)

        self._flower = ImageTk.PhotoImage(flower)
        self.create_image(590,30, image=self._flower)

    def update(self, checkpoint):
        """Updates checkpoint.

        Parameters:
            checkpoint (int): checkpoint to be updated.
        """
        if checkpoint == 2:
            self.create_rectangle(42,25,190,35,\
                                  fill='Medium Aquamarine')
        elif checkpoint == 3:
            self.update(2)
            self.create_rectangle(237,25,382,35,fill='Medium Aquamarine')
        elif checkpoint == 4:
            self.update(2)
            self.update(3)
            self.create_rectangle(417,25,565,35,fill='Medium Aquamarine')
        else:
            pass


class ButterflyDot(AbstractDot):
    """Abstract class for a dot without a kind"""
    DOT_NAME = "butterfly"
    
    def __init__(self, kind):
        super().__init__(kind)
        self.set_kind = kind
        self._activation = 0
        
    def get_view_id(self):
        return "{0}/{1}".format(self.get_name(), self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        if self._activation < 4:
            if self._activation == 0:
                self._kind = 'coocoon-cracked'
            if self._activation == 1:
                self._kind = 'butterfly-0'
            elif self._activation == 2:
                self._kind = 'butterfly-1'
            elif self._activation == 3:
                self._kind = 'butterfly-2'
            self._activation +=1
        else:
            self.activate(position, game, activated, has_loop=False)         

    def activate(self, position, game, activated, has_loop=False):
            game.grid[position].set_dot(None)
        
            adjacents = list(game.grid.get_adjacent_cells(position)) +\
              list(game.grid.get_adjacent_cells(position,deltas=game.grid.DIAGONAL_DELTAS))

            for cell in adjacents:
                try:
                    game.add_dots_to_score(game.grid[cell].get_dot())
                    game.grid[cell].get_dot().activate(cell,game,activated, has_loop=False)
                    game.grid[cell].set_dot(None)
                except Exception:
                    continue
            self._expired = True
            game.grid[position].set_dot(None)
            game.after_resolve()
               
    def after_resolved(self, position, game):
        pass

    def can_connect(self):
        if self._expired:
            return True
        return False


class SwirlDot(AbstractDot):
    """Abstract class for a dot without a kind"""
    DOT_NAME = "swirl"

    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        pass

    def activate(self, position, game, activated, has_loop=False):
        adjacents = list(game.grid.get_adjacent_cells(position)) +\
              list(game.grid.get_adjacent_cells(position,deltas=game.grid.DIAGONAL_DELTAS))
        for cell in adjacents:
                try:
                    kind = game.grid[position].get_dot().get_kind()
                    game.grid[cell].set_dot(BasicDot(kind))
                except Exception:
                    continue
        self._expired = False

    def after_resolved(self, position, game):
        pass

    def can_connect(self):
        return True


class AnchorDot(AbstractDot):
    """Abstract class for a dot without a kind"""
    DOT_NAME = "anchor"
    PRIORITY =  -10

    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        pass

    def activate(self, position, game, *args, has_loop=False):
        self._expired = True
        

    def after_resolved(self, position, game):
        if position[0] == 7:
            return [position]
            

    def can_connect(self):
        return False


class BalloonDot(AbstractDot):
    """Abstract class for a dot without a kind"""
    DOT_NAME = "balloon"
    PRIORITY = -10

    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        pass

    def activate(self, position, game, *args, has_loop=False):
        self._expired = True
        game.grid[position].set_dot(None)

    def after_resolved(self, position, game):
        if position[0] == 0:
            return [position]
        else:
            game.grid[position].swap_with(game.grid[(position[0]-1,position[1])])

    def can_connect(self):
        return False


class FlowerDot(AbstractDot):
    """Abstract class for a dot without a kind"""
    DOT_NAME = "flower"

    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        pass

    def activate(self, position, game, activated, has_loop=False):
        self._expired = True
        adjacents = list(game.grid.get_adjacent_cells(position)) +\
              list(game.grid.get_adjacent_cells(position,deltas=game.grid.DIAGONAL_DELTAS))
    
        for cell in adjacents:
            try:
                if game.grid[position].get_dot().get_kind() == game.grid[cell].get_dot().get_kind():
                    game.grid[cell].get_dot().activate(position, game, activated)
                    game.grid[cell].set_dot(None)
            except Exception:
                continue
        game.grid[position].set_dot(None)

    def after_resolved(self, position, game):
        pass

    def can_connect(self):
        return True


class CompanionDot(BasicDot):
    DOT_NAME = "companion"
    
    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.get_kind())
 
    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        pass

    def activate(self, position, game, activated, has_loop=False):
        game.companion.charge()
        self._expired = True

    def after_resolved(self, position, game):
        pass

    def can_connect(self):
        return True


class BeamDot(BasicDot):
    DOT_NAME = "beam"

    def __init__(self, kind, _type):
        super().__init__(kind)
        self._type = _type
        
    def get_view_id(self):
        return "{0}/{1}/{2}".format(self.DOT_NAME, self._type, self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        pass

    def activate(self, position, game, activated, has_loop=False):
        self._expired = True
        to_activated = set() 
    
        if self._type == 'x':
            for i in range(0,8):
                to_activated.add((position[0],i))
            
        elif self._type == 'y':
            to_activated = set()
            for i in range(0,8):
                to_activated.add((i,position[1]))

        else:
            to_activated = set()
            for i in range(0,8):
                to_activated.add((i,position[1]))
                to_activated.add((position[0],i))

        to_activated = list(to_activated)
        to_activated.remove(position)
        for cell in to_activated:
            try:
                if not isinstance(game.grid[position].get_dot(),BeamDot):
                    game.add_dots_to_score(game.grid[cell].get_dot())
                    game.grid[cell].get_dot().activate(cell,game,activated, has_loop=False)
                game.grid[cell].set_dot(None)
            except Exception:
                continue        
        game.grid[position].set_dot(None)
                     
    def after_resolved(self, position, game):
        pass

    def can_connect(self):
        return True


class TurtleDot(BasicDot):
    DOT_NAME = "turtle"
    PRIORITY = -10

    def __init__(self, kind, app):
        super().__init__(kind)
        self._is_enabled = True
        self._app = app
        
    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.get_kind())

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        if self._is_enabled:
            self._kind = 'shell'
        else:
            self._kind = 'turtle'
        self._is_enabled = not self._is_enabled
        
    def activate(self, position, game, *args, has_loop=False):
        return               

    def after_resolved(self, position, game):
        adjacents = list(game.grid.get_adjacent_cells(position)) +\
            list(game.grid.get_adjacent_cells(position,deltas=game.grid.DIAGONAL_DELTAS))

        availables = list(set(adjacents).difference(self._app.get_dead_cells()))
        if self._is_enabled:
            swap_cell = availables[random.randint(0,len(availables)-1)]
            game.grid[position].swap_with(game.grid[swap_cell])
            
    def can_connect(self):
        return False
    

class EskimoCompanion(AbstractCompanion):
    NAME = 'eskimo'
    _charge = 0

    def activate(self, game, app):
        swirls = list(app.generate_cells(6))
        kinds = app.get_dot_kinds()
        for pos in swirls:
            app._game.grid[pos].set_dot(SwirlDot(kinds[random.randint(0,3)]))


class AristotleCompanion(AbstractCompanion):
    NAME = 'aristotle'
    _charge = 0
      
    def activate(self, game, app):
        butterflies = list(app.generate_cells(6))
        for pos in butterflies:
            app._game.grid[pos].set_dot(ButterflyDot('coocoon'))
        
         
class BuffaloCompanion(AbstractCompanion):
    NAME = 'buffalo'
    _charge = 0

    def activate(self, game, app):
        wildcards = list(app.generate_cells(6))
        for pos in wildcards:
            app._game.grid[pos].set_dot(WildcardDot())


class CaptainCompanion(AbstractCompanion):
    NAME = 'captain'
    _charge = 0

    def activate(self, game, app):
        beams = list(app.generate_cells(6))
        kinds = app.get_dot_kinds()
        types = ['x','y','xy']
        for pos in beams:
            app._game.grid[pos].set_dot(BeamDot(kinds[random.randint(0,3)],\
                                        types[random.randint(0,2)]))


class GoatCompanion(AbstractCompanion):
    NAME = 'goat'
    _charge = 0

    def get_most(self, game, app):
        """Returns the most common kind of dots on the grid."""
        dots = {}
        kinds = app.get_dot_kinds()
        for kind in kinds:
            dots[kind] = []
            for pos in app.get_grid():
                if game.grid[pos].get_dot().get_kind() == kind:
                    dots[kind].append(pos)
        most_kind, most_value = max(dots.items(), key = lambda x: len(set(x[1])))
        return most_kind

    def activate(self, game, app):
        for pos in list(app.generate_cells(8)):
            game.grid[pos].set_dot(BasicDot(self.get_most(game,app)))


class DeerCompanion(GoatCompanion):
    NAME = 'deer'
    _charge = 0

    def activate(self, game, app):
        place = list(app.generate_cells(0))[0]
        adjacents = list(game.grid.get_adjacent_cells(place)) + list(place) +\
            list(game.grid.get_adjacent_cells(place,deltas=game.grid.DIAGONAL_DELTAS))
        
        for cell in adjacents:
            try:
                game.grid[cell].set_dot(BasicDot(self.get_most(game,app)))
            except Exception:
                continue

         
class PenguinCompanion(AbstractCompanion):
    NAME = 'penguin'
    _charge = 0

    def activate(self, game, app):
        kind = app.get_dot_kinds()[random.randint(0,3)]

        return game.activate_all(set([x for x in app.get_grid() if game.grid[x].get_dot().get_kind() == kind]),\
                                 has_loop=True)

    
def main():
    """Sets-up the GUI for Dots & Co"""
    # Write your GUI instantiation code here
    app = Manager()
    app.mainloop()


if __name__ == "__main__":
    main()
