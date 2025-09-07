from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys

camera_pos = (0, -200, 150)
player_pos = [0, 0, 0]
player_direction = 0
player_speed = 12
GRID_LENGTH = 950
first_person_view = False
top_view = False
zoom_level = 1
max_zoom = 3.0

is_jumping = False
jump_velocity = 0
gravity = -2.0
jump_strength = 12.0  # Increased for higher jump (approximately 36 units high)
max_jump_height = 40  # Player can now jump much higher
ground_level = 0

# Key state tracking for combination moves
w_key_pressed = False
space_key_pressed = False

# Font constant
FONT = 4  # GLUT_BITMAP_HELVETICA_18 equivalent

# Cheat mode variables
cheat_mode = False
god_mode = False
wall_walk_mode = False
player_health = 100
max_health = 100

# Life system variables
player_lives = 3
max_lives = 3
respawn_timer = 0
showing_respawn_message = False
respawn_delay = 300  # 5 seconds at 60 FPS
death_position = [0, 0, 0]  # Position where player died
death_cause = ""  # Track what caused the player's death

# Game objects
treasure_collected = False
treasure_pos = [0, 0, 20]
door_pos = [0, 0, 0]  # Exit door position
near_treasure = False  # Player is near treasure
near_door = False      # Player is near door (after collecting treasure)
police_positions = []
police_directions = []
police_movement_timers = []  # Timer for random direction changes
game_over = False
level_complete = False
showing_escape_message = False
waiting_for_next_level = False
score = 0
police_patrol_range = 900

# Laser system variables
lasers = []
laser_disabled = False

# Maze configuration
WALL_HEIGHT = 100
WALL_THICKNESS = 50
PLAYER_RADIUS = 8  # Reduced from 15 to allow better movement in corridors
COLLISION_MARGIN = 0  # Removed margin to eliminate invisible walls
POLICE_RADIUS = 15

# Maze layout (1 = wall, 0 = path)
maze = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,1,0,1,0,0,0,0,1],
    [1,0,1,1,0,1,0,1,0,1,1,1,0,1,1],
    [1,0,1,0,0,1,0,0,0,0,0,1,0,0,1],
    [1,0,1,0,1,1,0,0,1,1,0,1,1,0,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,0,1],
    [1,0,1,0,1,1,0,1,1,0,1,1,0,1,1],
    [1,0,0,0,0,1,0,0,0,0,0,1,0,0,1],
    [1,0,1,1,0,1,0,0,1,1,0,1,1,0,1],
    [1,0,1,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,1,1,1,1,0,1,0,1,0,1,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,0,1],
    [1,1,0,0,1,1,0,1,1,1,0,1,0,1,1],
    [1,0,0,0,0,1,0,0,0,0,0,1,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

# Door positions (row, col) - No static doors, only dynamic escape door
DOOR_POSITIONS = [
]

# Colors
WALL_COLOR = (1, 1, 1)
WALL_COLOR_CHEAT = (1.0, 1.0, 1.0, 0.3)  # Transparent walls in cheat mode
WALL_BORDER_COLOR = (0, 0, 0)
WALL_BORDER_COLOR_CHEAT = (0.5, 0.5, 0.5, 0.3)  # Transparent borders in cheat mode
DOOR_COLOR = (0.2, 0.4, 0.9)
FLOOR_COLOR = (0.25, 0.25, 0.25)
GRID_COLOR = (0.35, 0.35, 0.35)
PLAYER_TOP_COLOR = (1.0, 0.75, 0.8)  # Light pink
POLICE_COLOR = (0.0, 0.0, 1.0)
TREASURE_COLOR = (1.0, 0.84, 0.0)
BULLET_COLOR = (1.0, 0.0, 0.0)
CHEAT_COLOR = (1.0, 0.84, 0.0)  # Gold for cheat mode indicators
LASER_COLOR = (1.0, 0.0, 0.0)  # Red laser beam
LASER_EMITTER_COLOR = (1.0, 0.5, 0.0)  # Orange laser emitters
# Game objects
wall_boundaries = []
maze_width = 0
maze_height = 0
maze_offset_x = 0
maze_offset_y = 0

police_original_positions = []

# Add these to your game state variables
level = 1
level_message_timer = 0
showing_level_message = False
num_police = 2  # Starting number of police
waiting_for_enter = False

# Timing system variables
level_time_limit = 180  # Starting time for level 1 (120 seconds)
level_time_remaining = 180
level_timer_active = False
timer_frames = 0  # Counter for frames to track seconds

# Path tracking system
visited_paths = set()  # Set to store visited path coordinates
path_track_size = 25   # Size of the tracking area around player

def init_3d():
    """Initialize OpenGL 3D settings including lighting"""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 10, 0, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.9, 0.9, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.5, 0.5, 0.5, 1))
    
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    init_wall_boundaries()
    place_game_objects()

def update_lighting():
    """Update the light position to maintain consistent lighting"""
    # Position the light in the scene
    glPushMatrix()
    glLoadIdentity()
    
    # Position light slightly above and in front of the camera
    light_pos = [camera_pos[0], camera_pos[1], camera_pos[2] + 50, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    
    glPopMatrix()

def place_game_objects():
    """Place treasure, door and police in valid positions"""
    global treasure_pos, door_pos, police_positions, police_directions, police_original_positions, police_movement_timers
    
    rows, cols = len(maze), len(maze[0])
    cell_size = WALL_THICKNESS * 2
    
    # Find all open positions
    open_positions = []
    for i in range(rows):
        for j in range(cols):
            if maze[i][j] == 0:
                x = maze_offset_x + j * cell_size + cell_size/2
                y = maze_offset_y + i * cell_size + cell_size/2
                open_positions.append((x, y))
    
    # Place treasure (ensure it's not at starting position)
    if len(open_positions) > 1:
        treasure_pos[0], treasure_pos[1] = random.choice(open_positions[1:])
        open_positions.remove((treasure_pos[0], treasure_pos[1]))
    
    # Place door (ensure it's not at starting position or treasure position)
    if len(open_positions) > 1:
        door_pos[0], door_pos[1] = random.choice(open_positions[1:])
        door_pos[2] = 25  # Height for door
        open_positions.remove((door_pos[0], door_pos[1]))
    
    # Place police officers (number based on current level)
    police_positions = []
    police_directions = []
    police_original_positions = []
    police_movement_timers = []
    for _ in range(num_police):
        if len(open_positions) > 0:
            x, y = random.choice(open_positions)
            police_positions.append([x, y, 0])
            li=[0,90,180,270]
            dir=random.choice(li)
            police_directions.append(dir)
            police_original_positions.append([x, y])  # Store original position for patrol
            police_movement_timers.append(0)  # Initialize movement timer
            open_positions.remove((x, y))
    
    # Initialize lasers based on level
    init_lasers()

def init_lasers():
    """Initialize lasers based on current level"""
    global lasers
    
    # Clear existing lasers
    lasers = []
    
    # Predefined laser configurations (x1, z1, x2, z2, movement_type)
    # Coordinates are in maze world space, adjusted for 15x15 maze
    base_laser_configs = [
        (-200, -200, -50, -200, 'horizontal_fixed'),   # Level 1: 2 lasers
        (100, -300, 100, -150, 'vertical_fixed'),
        (-300, 150, -150, 150, 'horizontal_fixed'),    # Level 2: 3 lasers  
        (-450, -450, -450, -300, 'vertical_fixed'),    # Level 3: 4 lasers
        (300, 50, 450, 50, 'horizontal_fixed'),        # Level 4: 5 lasers
        (0, -450, 150, -450, 'horizontal_fixed'),      # Level 5: 6 lasers
        (-450, 0, -450, 150, 'vertical_fixed'),        # Level 6: 7 lasers
        (350, -150, 350, 0, 'vertical_fixed'),         # Level 7: 8 lasers
    ]
    
    # Calculate number of lasers for current level (start with 2, increase by 1 each level)
    num_lasers = min(1 + level, len(base_laser_configs))
    
    # Create lasers for current level
    for i in range(num_lasers):
        config = base_laser_configs[i]
        laser = Laser(config[0], config[1], config[2], config[3], config[4])
        lasers.append(laser)

def init_wall_boundaries():
    """Pre-calculate wall boundaries for collision detection"""
    global wall_boundaries, maze_width, maze_height, maze_offset_x, maze_offset_y
    
    rows, cols = len(maze), len(maze[0])
    cell_size = WALL_THICKNESS * 2
    
    maze_offset_x, maze_offset_y = -cols * WALL_THICKNESS, -rows * WALL_THICKNESS
    maze_width, maze_height = cols * cell_size, rows * cell_size

    wall_boundaries = []
    
    for i in range(rows):
        for j in range(cols):
            if maze[i][j] == 1:
                is_door = (i, j) in DOOR_POSITIONS
                # Calculate wall position to match how walls are actually drawn
                x = maze_offset_x + j * cell_size
                y = maze_offset_y + i * cell_size
                
                # Walls are drawn centered at (x + WALL_THICKNESS/2, y + WALL_THICKNESS/2) 
                # and scaled by cell_size, so they actually occupy:
                # From (center - cell_size/2) to (center + cell_size/2)
                center_x = x + WALL_THICKNESS/2
                center_y = y + WALL_THICKNESS/2
                
                wall_boundaries.append((
                    center_x - cell_size/2,  # Left edge
                    center_y - cell_size/2,  # Bottom edge
                    center_x + cell_size/2,  # Right edge
                    center_y + cell_size/2,  # Top edge
                    is_door
                ))

def check_maze_perimeter(x, y):
    """Check if position is within maze perimeter"""
    return (maze_offset_x <= x <= maze_offset_x + maze_width and 
            maze_offset_y <= y <= maze_offset_y + maze_height)

def draw_door(x, y, z, cell_size, wall_thickness, wall_height, orientation):
    """Draw a door on a wall"""
    door_width = cell_size * 0.6  # Made door wider (was 0.4, now 0.6)
    door_height = cell_size * 0.7
    
    # Enable blending for transparency in cheat mode
    if cheat_mode:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(DOOR_COLOR[0], DOOR_COLOR[1], DOOR_COLOR[2], 0.3)  # Transparent door in cheat mode
    else:
        glColor3f(*DOOR_COLOR)
    
    if orientation == 'vertical':
        glPushMatrix()
        glTranslatef(x, y + wall_thickness/2, z + wall_height/2)
        glScalef(door_width, wall_thickness*1.5, door_height)  # Made door thicker (was 0.5, now 1.5)
        glutSolidCube(1.0)
        glDisable(GL_LIGHTING)
        
        if cheat_mode:
            glColor4f(WALL_BORDER_COLOR_CHEAT[0], WALL_BORDER_COLOR_CHEAT[1], WALL_BORDER_COLOR_CHEAT[2], 0.3)
        else:
            glColor3f(*WALL_BORDER_COLOR)
            
        glutWireCube(1.01)
        glEnable(GL_LIGHTING)
        glPopMatrix()
    else:
        glPushMatrix()
        glTranslatef(x + wall_thickness/2, y, z + wall_height/2)
        glScalef(wall_thickness*1.5, door_width, door_height)  # Made door thicker (was 0.5, now 1.5)
        glutSolidCube(1.0)
        glDisable(GL_LIGHTING)
        
        if cheat_mode:
            glColor4f(WALL_BORDER_COLOR_CHEAT[0], WALL_BORDER_COLOR_CHEAT[1], WALL_BORDER_COLOR_CHEAT[2], 0.3)
        else:
            glColor3f(*WALL_BORDER_COLOR)
            
        glutWireCube(1.01)
        glEnable(GL_LIGHTING)
        glPopMatrix()
    
    # Disable blending after drawing door
    if cheat_mode:
        glDisable(GL_BLEND)

def draw_text(x, y, text, font_size='medium', color=(1, 1, 1)):
    """Draw text on screen with specified color"""
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    
    # Try to get the proper GLUT font constant
    try:
        # Import font constants
        from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
        font = GLUT_BITMAP_HELVETICA_18
    except ImportError:
        # Fallback to a working font
        try:
            from OpenGL.GLUT import GLUT_BITMAP_8_BY_13
            font = GLUT_BITMAP_8_BY_13
        except ImportError:
            # Use a numeric constant that should work
            import ctypes
            font = ctypes.cast(0x0004, ctypes.c_void_p)
    
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_health_bar():
    """Draw player health bar"""
    if cheat_mode and god_mode:
        return  # Don't show health bar in god mode
    
    # Health bar background
    glDisable(GL_LIGHTING)
    glColor3f(0.3, 0.3, 0.3)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background bar
    glBegin(GL_QUADS)
    glVertex2f(20, 50)
    glVertex2f(220, 50)
    glVertex2f(220, 70)
    glVertex2f(20, 70)
    glEnd()
    
    # Health bar
    health_ratio = player_health / max_health
    if health_ratio > 0.6:
        glColor3f(0.0, 1.0, 0.0)  # Green
    elif health_ratio > 0.3:
        glColor3f(1.0, 1.0, 0.0)  # Yellow
    else:
        glColor3f(1.0, 0.0, 0.0)  # Red
    
    glBegin(GL_QUADS)
    glVertex2f(20, 50)
    glVertex2f(20 + 200 * health_ratio, 50)
    glVertex2f(20 + 200 * health_ratio, 70)
    glVertex2f(20, 70)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)

def draw_cheat_indicators():
    """Draw visual indicators when cheats are active"""
    if not cheat_mode:
        return
    
    # Draw cheat mode border
    glDisable(GL_LIGHTING)
    glColor3f(*CHEAT_COLOR)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw border around screen
    glBegin(GL_LINE_LOOP)
    glVertex2f(5, 5)
    glVertex2f(995, 5)
    glVertex2f(995, 795)
    glVertex2f(5, 795)
    glEnd()
    
    glBegin(GL_LINE_LOOP)
    glVertex2f(10, 10)
    glVertex2f(990, 10)
    glVertex2f(990, 790)
    glVertex2f(10, 790)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)

def draw_player():
    """Draw the player character"""
    if first_person_view:
        return
    
    # Change player color if in cheat mode
    player_color = CHEAT_COLOR if cheat_mode else PLAYER_TOP_COLOR
    
    if top_view:
        glPushMatrix()
        glTranslatef(player_pos[0], player_pos[1], player_pos[2] + 5)
        glColor3f(*player_color)
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(PLAYER_RADIUS, 5, 16, 1)
        glPopMatrix()
        glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glRotatef(player_direction, 0, 0, 1)
        glTranslatef(PLAYER_RADIUS * 0.5, 0, 2.5)
        glScalef(PLAYER_RADIUS, PLAYER_RADIUS/3, 5)
        glutSolidCube(1.0)
        glPopMatrix()
        glPopMatrix()
        return
    glPushMatrix()
    glTranslatef(*player_pos)
    glRotatef(player_direction, 0, 0, 1)
    glRotatef(-90, 0, 0, 1)
   
    # Head
    glPushMatrix()
    glColor3f(0.95, 0.75, 0.65)
    glTranslatef(0, 0, 70)
    glutSolidSphere(10, 16, 16)
    glPopMatrix()
   
    # Torso (change color if cheating)
    glPushMatrix()
    if cheat_mode:
        glColor3f(*CHEAT_COLOR)
    else:
        glColor3f(1.2, 0.72, 0.8)
    glTranslatef(0, 0, 45)
    glScalef(20, 12, 30)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Arms
    glPushMatrix()
    if cheat_mode:
        glColor3f(*CHEAT_COLOR)
    else:
        glColor3f(0.95, 0.75, 0.65)
    glTranslatef(12, 0, 45)
    glScalef(4, 4, 20)
    glutSolidCube(1.0)
    glPopMatrix()
   
    glPushMatrix()
    if cheat_mode:
        glColor3f(*CHEAT_COLOR)
    else:
        glColor3f(0.95, 0.75, 0.65)
    glTranslatef(-12, 0, 45)
    glScalef(4, 4, 20)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Legs
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.3)
    glTranslatef(7, 0, 15)
    glScalef(6, 6, 30)
    glutSolidCube(1.0)
    glPopMatrix()
   
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.3)
    glTranslatef(-7, 0, 15)
    glScalef(6, 6, 30)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Neck
    glPushMatrix()
    glColor3f(0.95, 0.75, 0.65)
    glTranslatef(0, 0, 65)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 4, 5, 10, 2)
    glPopMatrix()
   
    glPopMatrix()

def draw_police():
    """Draw police NPCs with guns, hands, and legs"""
    for i, pos in enumerate(police_positions):
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glRotatef(police_directions[i], 0, 0, 1)
        glRotatef(-90, 0, 0, 1)
        
        # Body
        glColor3f(*POLICE_COLOR)
        glPushMatrix()
        glTranslatef(0, 0, 45)
        glScalef(20, 12, 30)  
        glutSolidCube(1.0)       
        glPopMatrix()
        
        # Head
        glColor3f(0.95, 0.75, 0.65)
        glPushMatrix()
        glTranslatef(0, 0, 70) 
        glutSolidSphere(10, 16, 16)
        glPopMatrix()
        
        # Hat - white cone
        glColor3f(1.0, 1.0, 1.0)  # White color
        glPushMatrix()
        glTranslatef(0, 0, 80)
        glRotatef(-90, 1, 0, 0)
        glutSolidCone(12, 15, 16, 8)  # Cone with base radius 12, height 15
        glPopMatrix()
        
        # Right arm
        glPushMatrix()
        glColor3f(0.95, 0.75, 0.65)
        glTranslatef(10,0,10)          
        gluCylinder(gluNewQuadric(), 2, 2, 40, 32, 32)
        glPopMatrix()

        # Left arm 
        glPushMatrix()
        glColor3f(0.95, 0.75, 0.65)
        glTranslatef(-10, 30,80)      
        glRotatef(130, 1, 0, 0)      
        gluCylinder(gluNewQuadric(), 2,2, 40, 32, 32)
        glPopMatrix()       
        
        # Gun
        glPushMatrix()
        glColor3f(1.0, 0.5, 0.3)
        glTranslatef(-10, 56,97)      
        glRotatef(130, 1, 0, 0)    
        gluCylinder(gluNewQuadric(), 2,2, 40, 32, 32)
        glPopMatrix()   

        # Right leg
        glPushMatrix()
        glColor3f(*POLICE_COLOR)
        glTranslatef(10,0,-10)          
        gluCylinder(gluNewQuadric(), 2, 2, 35, 32, 32)
        glPopMatrix()

        # Left leg
        glPushMatrix()
        glColor3f(*POLICE_COLOR)
        glTranslatef(-10, 0,-10)      
        gluCylinder(gluNewQuadric(), 2,2, 35, 32, 32)
        glPopMatrix() 

        glPopMatrix() 

def draw_treasure():
    """Draw the treasure chest"""
    if treasure_collected:
        return
        
    glPushMatrix()
    glTranslatef(*treasure_pos)
    glColor3f(*TREASURE_COLOR)
    
    # Main chest
    glPushMatrix()
    glScalef(30, 20, 15)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Lid
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glScalef(30, 20, 5)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Lock
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, -12, 10)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def draw_escape_door():
    """Draw the escape door"""
    glPushMatrix()
    glTranslatef(*door_pos)
    glColor3f(*DOOR_COLOR)
    
    # Door frame
    glPushMatrix()
    glScalef(35, 10, 50)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Door handle
    glColor3f(1.0, 1.0, 0.0)  # Golden handle
    glPushMatrix()
    glTranslatef(-15, 0, 0)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def draw_lasers():
    """Draw all laser security systems"""
    if laser_disabled:
        return
    
    for laser in lasers:
        laser.draw()

def draw_maze():
    """Draw the maze with walls and doors"""
    rows = len(maze)
    cols = len(maze[0])
    cell_size = WALL_THICKNESS * 2
    
    offset_x = maze_offset_x
    offset_y = maze_offset_y
    
    # Enable blending for transparency in cheat mode
    if cheat_mode:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        wall_color = WALL_COLOR_CHEAT
        border_color = WALL_BORDER_COLOR_CHEAT
    else:
        wall_color = WALL_COLOR
        border_color = WALL_BORDER_COLOR
    
    for i in range(rows):
        for j in range(cols):
            if maze[i][j] == 1:
                x = offset_x + j * cell_size
                y = offset_y + i * cell_size
                z = 0
                
                glPushMatrix()
                glTranslatef(x + WALL_THICKNESS/2, y + WALL_THICKNESS/2, z + WALL_HEIGHT/2)
                
                # Set color with alpha for transparency
                if cheat_mode:
                    glColor4f(*wall_color)
                else:
                    glColor3f(*wall_color)
                    
                glScalef(cell_size, cell_size, WALL_HEIGHT)
                glutSolidCube(1.0)
                
                glDisable(GL_LIGHTING)
                
                # Set border color with alpha for transparency
                if cheat_mode:
                    glColor4f(*border_color)
                else:
                    glColor3f(*border_color)
                    
                glutWireCube(1.01)
                glEnable(GL_LIGHTING)
                glPopMatrix()
    
    # Disable blending after drawing walls
    if cheat_mode:
        glDisable(GL_BLEND)
    
    # Draw doors
    for door_i, door_j in DOOR_POSITIONS:
        if 0 <= door_i < rows and 0 <= door_j < cols and maze[door_i][door_j] == 1:
            x = offset_x + door_j * cell_size
            y = offset_y + door_i * cell_size
            z = 0
            
            if door_j < cols - 1 and maze[door_i][door_j + 1] == 0:
                draw_door(x + cell_size - WALL_THICKNESS/2, y, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'vertical')
            elif door_j > 0 and maze[door_i][door_j - 1] == 0:
                draw_door(x - WALL_THICKNESS/2, y, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'vertical')
            elif door_i < rows - 1 and maze[door_i + 1][door_j] == 0:
                draw_door(x, y + cell_size - WALL_THICKNESS/2, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'horizontal')
            elif door_i > 0 and maze[door_i - 1][door_j] == 0:
                draw_door(x, y - WALL_THICKNESS/2, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'horizontal')
            else:
                draw_door(x + cell_size - WALL_THICKNESS/2, y, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'vertical')

def draw_floor():
    """Draw the floor grid"""
    # Calculate maze boundaries for floor
    maze_min_x = maze_offset_x
    maze_max_x = maze_offset_x + maze_width
    maze_min_y = maze_offset_y
    maze_max_y = maze_offset_y + maze_height
    
    # Draw floor only within maze boundaries
    glColor3f(*FLOOR_COLOR)
    glBegin(GL_QUADS)
    glVertex3f(maze_min_x, maze_min_y, 0)
    glVertex3f(maze_max_x, maze_min_y, 0)
    glVertex3f(maze_max_x, maze_max_y, 0)
    glVertex3f(maze_min_x, maze_max_y, 0)
    glEnd()
   
    # Draw grid only within maze boundaries
    glColor3f(*GRID_COLOR)
    glBegin(GL_LINES)
    
    # Calculate maze boundaries
    maze_min_x = maze_offset_x
    maze_max_x = maze_offset_x + maze_width
    maze_min_y = maze_offset_y
    maze_max_y = maze_offset_y + maze_height
    
    # Vertical grid lines (only within maze bounds)
    x = maze_min_x
    while x <= maze_max_x:
        if x % 50 == 0:  # Draw every 50 units to match cell size
            glVertex3f(x, maze_min_y, 1)
            glVertex3f(x, maze_max_y, 1)
        x += 50
    
    # Horizontal grid lines (only within maze bounds)
    y = maze_min_y
    while y <= maze_max_y:
        if y % 50 == 0:  # Draw every 50 units to match cell size
            glVertex3f(maze_min_x, y, 1)
            glVertex3f(maze_max_x, y, 1)
        y += 50
    
    glEnd()
    
def is_point_in_wall(x, y, radius=0):
    """Check if a point is inside a wall with optional radius"""
    for min_x, min_y, max_x, max_y, is_door in wall_boundaries:
        if (x + radius > min_x and 
            x - radius < max_x and 
            y + radius > min_y and 
            y - radius < max_y):
            return True
    return False

def check_wall_collision(new_x, new_y):
    """Improved collision detection with sliding and minimal boundary checking"""
    # In wall walk mode, only check maze perimeter
    if cheat_mode and wall_walk_mode:
        if not check_maze_perimeter(new_x, new_y):
            return player_pos[0], player_pos[1], False
        return new_x, new_y, True
    
    current_x, current_y = player_pos[0], player_pos[1]
    
    # Use the exact player radius with a small safety margin to prevent wall penetration
    effective_radius = PLAYER_RADIUS + 2  # Add small safety margin
    
    # Check if the new position would cause collision
    if is_point_in_wall(new_x, new_y, effective_radius):
        
        # Try moving only in X direction with safety check
        if not is_point_in_wall(new_x, current_y, effective_radius):
            return new_x, current_y, True
        
        # Try moving only in Y direction with safety check
        if not is_point_in_wall(current_x, new_y, effective_radius):
            return current_x, new_y, True
        
        # If both axes collide, stay in place
        return current_x, current_y, False
    
    # Movement is safe
    return new_x, new_y, True

def movement_with_collision_detection(dx, dy):
    """Move player with collision detection"""
    current_x, current_y = player_pos[0], player_pos[1]
    new_x, new_y = current_x + dx, current_y + dy
    
    # Normal collision detection
    result = check_wall_collision(new_x, new_y)
    if result is None: return False
        
    final_x, final_y, moved = result
    
    player_pos[0] = final_x
    player_pos[1] = final_y
    
    # Update visited paths when player moves
    if moved:
        update_visited_paths()
    
    return moved

def move_police():
    """Move police NPCs with intelligent maze navigation"""
    
    for i in range(len(police_positions)):
        current_x, current_y, _ = police_positions[i]
        
        # Increment movement timer
        police_movement_timers[i] += 1
        
        # Occasionally change direction randomly (every 120-300 frames, i.e., 2-5 seconds at 60fps)
        if police_movement_timers[i] > random.randint(120, 300):
            police_movement_timers[i] = 0
            # Random direction change for more dynamic movement
            if random.random() < 0.3:  # 30% chance to change direction
                police_directions[i] = random.randint(0, 359)
        
        # Calculate movement based on current direction
        dx = math.cos(math.radians(police_directions[i])) * 0.8
        dy = math.sin(math.radians(police_directions[i])) * 0.8
        
        new_x = current_x + dx
        new_y = current_y + dy
        
        # Check for wall collisions
        if not is_point_in_wall(new_x, new_y, POLICE_RADIUS):
            police_positions[i][0] = new_x
            police_positions[i][1] = new_y
        else:
            # Simple turning strategy when hitting a wall
            # Randomly choose between: left turn, right turn, or 180 degree turn
            turn_options = [
                (police_directions[i] - 90) % 360,   # Turn left
                (police_directions[i] + 90) % 360,   # Turn right  
                (police_directions[i] + 180) % 360   # Turn around 180 degrees
            ]
            
            # Randomly select one of the three turning options
            police_directions[i] = random.choice(turn_options)

def update_lasers():
    """Update all laser movements"""
    global lasers
    for laser in lasers:
        laser.update()

def check_laser_collision():
    """Check if player collides with any laser"""
    global game_over, player_health, player_lives, respawn_timer, showing_respawn_message
    global death_position
    
    # Skip laser collision if in god mode
    if cheat_mode and god_mode:
        return
    
    # Skip if lasers are disabled
    if laser_disabled:
        return
    
    # Check if player is jumping - ANY jump height should avoid lasers
    if is_jumping and player_pos[2] > 5:
        # Player is jumping - no laser collision at all
        return
    
    # Extra safety check for any height above ground
    if player_pos[2] > 8:
        # Player is clearly above ground level - no laser collision
        return
    
    for laser in lasers:
        if laser.check_collision(player_pos[0], player_pos[1], player_pos[2]):
            # Player hit by laser - instant game over (no lives left)
            global death_cause
            death_position = player_pos.copy()
            death_cause = "laser"
            player_lives = 0  # Set lives to 0 for instant game over
            game_over = True
            break

def jump():
    """Initiate player jump if not already jumping"""
    global is_jumping, jump_velocity, player_pos
    
    # Can only jump if on ground (not already jumping)
    if not is_jumping and player_pos[2] <= ground_level:
        is_jumping = True
        jump_velocity = jump_strength
        
        # Add automatic forward movement during jump (2 grid cells)
        jump_forward_speed = 200.0  # Move forward 2 grid cells (each cell is 100 units)
        forward_x = math.cos(math.radians(player_direction)) * jump_forward_speed
        forward_y = math.sin(math.radians(player_direction)) * jump_forward_speed
        
        # Apply forward movement with collision detection
        movement_with_collision_detection(forward_x, forward_y)

def update_jump():
    """Update jump physics"""
    global is_jumping, jump_velocity, player_pos
    
    if is_jumping:
        # Update vertical position
        player_pos[2] += jump_velocity
        
        # Apply gravity
        jump_velocity += gravity
        
        # Check if reached maximum height (can't jump higher than walls)
        if player_pos[2] >= max_jump_height:
            player_pos[2] = max_jump_height
            jump_velocity = min(jump_velocity, 0)  # Only allow falling
        
        # Check if landed on ground
        if player_pos[2] <= ground_level:
            player_pos[2] = ground_level
            is_jumping = False
            jump_velocity = 0

def check_police_detection():
    """Check if player is in any police detection zone"""
    global game_over, player_health, player_lives, respawn_timer, showing_respawn_message
    
    # Skip detection if in god mode
    if cheat_mode and god_mode:
        return
    
    for police in police_positions:
        px, py, pz = police
        player_x, player_y, _ = player_pos
        
        # Calculate distance to player
        dist_to_player = math.sqrt((px - player_x)**2 + (py - player_y)**2)
        
        # If player is in detection range (150 units)
        if dist_to_player < 150:
            if not (cheat_mode and god_mode):
                # Reduce health instead of immediate game over
                player_health -= 2
                if player_health <= 0:
                    handle_player_death()
            return

def draw_police_detection_zone():
    """Draw red circles showing police detection zones"""
    # Don't show detection zones in god mode
    if cheat_mode and god_mode:
        return
        
    glDisable(GL_LIGHTING)
    for police in police_positions:
        px, py, pz = police
        glColor3f(1.0, 0.0, 0.0)  # Red color
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(px, py, 1)  # Center point
        for angle in range(0, 361, 10):
            rad = math.radians(angle)
            x = px + 150 * math.cos(rad)  # 150 is detection radius
            y = py + 150 * math.sin(rad)
            glVertex3f(x, y, 1)  # Slightly above floor to avoid z-fighting
        glEnd()
    glEnable(GL_LIGHTING)

def toggle_cheat_mode():
    """Toggle cheat mode on/off - automatically enables all cheat features"""
    global cheat_mode, god_mode, wall_walk_mode, player_health, laser_disabled
    
    cheat_mode = not cheat_mode
    
    if cheat_mode:
        # Enable all cheat features automatically
        god_mode = True
        wall_walk_mode = True
        laser_disabled = True  # Disable lasers in cheat mode
        player_health = max_health  # Restore full health
    else:
        # Disable all cheat features
        god_mode = False
        wall_walk_mode = False
        laser_disabled = False  # Re-enable lasers when cheat mode is off

def init_level_timer():
    """Initialize timer for current level"""
    global level_time_limit, level_time_remaining, level_timer_active, timer_frames
    
    # Calculate time limit: 120 seconds for level 1, reduce by 10 seconds each level
    # Minimum time limit of 30 seconds
    level_time_limit = max(30, 180 - (level - 1) * 10)
    level_time_remaining = level_time_limit
    level_timer_active = True
    timer_frames = 0

def update_timer():
    """Update the level timer"""
    global level_time_remaining, timer_frames, game_over, level_timer_active, player_lives
    
    if not level_timer_active or game_over or showing_level_message or showing_respawn_message or cheat_mode:
        return
    
    # Count frames (assuming 60 FPS, so 60 frames = 1 second)
    timer_frames += 1
    if timer_frames >= 60:
        timer_frames = 0
        level_time_remaining -= 1
        
        # Check if time is up - game over immediately
        if level_time_remaining <= 0:
            global death_cause
            death_cause = "time"
            player_lives = 0  # Set lives to 0 when time runs out
            game_over = True
            level_timer_active = False

def get_timer_color():
    """Get color for timer display based on remaining time"""
    if level_time_remaining > level_time_limit * 0.5:
        return (0.0, 1.0, 0.0)  # Green
    elif level_time_remaining > level_time_limit * 0.25:
        return (1.0, 1.0, 0.0)  # Yellow
    else:
        return (1.0, 0.0, 0.0)  # Red

def format_time(seconds):
    """Format time as MM:SS"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def update_visited_paths():
    """Update the visited paths based on player position"""
    global visited_paths
    
    # Get player's current maze grid position
    cell_size = WALL_THICKNESS * 2
    grid_x = int((player_pos[0] - maze_offset_x) // cell_size)
    grid_y = int((player_pos[1] - maze_offset_y) // cell_size)
    
    # Check if position is valid and is a path (not a wall)
    if (0 <= grid_y < len(maze) and 
        0 <= grid_x < len(maze[0]) and 
        maze[grid_y][grid_x] == 0):
        visited_paths.add((grid_x, grid_y))

def clear_visited_paths():
    """Clear all visited paths (used when starting new level or resetting)"""
    global visited_paths
    visited_paths.clear()

def handle_player_death():
    """Handle player death - lose a life and respawn or game over"""
    global player_lives, player_health, respawn_timer, showing_respawn_message, game_over, level_timer_active, death_position, death_cause
    
    # Store the position where player died
    death_position = [player_pos[0], player_pos[1], player_pos[2]]
    death_cause = "police"  # Death caused by police
    
    player_lives -= 1
    level_timer_active = False  # Pause timer during respawn
    
    if player_lives > 0:
        # Still have lives left - show respawn message and start countdown
        showing_respawn_message = True
        respawn_timer = respawn_delay
    else:
        # No lives left - game over
        game_over = True

def respawn_police_randomly():
    """Respawn police at random valid maze positions, avoiding the death position"""
    global police_positions, police_directions, police_original_positions, police_movement_timers
    
    # Find valid positions for police (where maze is 0)
    valid_positions = []
    cell_size = WALL_THICKNESS * 2
    
    # Convert death position to grid coordinates for comparison
    death_grid_x = int((death_position[0] - maze_offset_x) / cell_size)
    death_grid_y = int((death_position[1] - maze_offset_y) / cell_size)
    
    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j] == 0:  # Empty space
                # Skip positions too close to death position (within 2 cells)
                if abs(j - death_grid_x) <= 2 and abs(i - death_grid_y) <= 2:
                    continue
                
                # Convert to world coordinates
                x = maze_offset_x + j * cell_size + cell_size/2
                y = maze_offset_y + i * cell_size + cell_size/2
                valid_positions.append((x, y))
    
    # Respawn all police at random positions
    for i in range(len(police_positions)):
        if len(valid_positions) > 0:
            # Select a random position and remove it to avoid duplicates
            pos_index = random.randint(0, len(valid_positions) - 1)
            x, y = valid_positions.pop(pos_index)
            police_positions[i] = [x, y, 0]
            police_original_positions[i] = [x, y]
            
            # Random direction for each police
            li = [0, 90, 180, 270]
            police_directions[i] = random.choice(li)
            police_movement_timers[i] = 0  # Reset movement timer
        else:
            # Fallback: if no positions far enough, use any valid position except exact death spot
            fallback_positions = []
            for i_maze in range(len(maze)):
                for j_maze in range(len(maze[0])):
                    if maze[i_maze][j_maze] == 0 and not (j_maze == death_grid_x and i_maze == death_grid_y):
                        x = maze_offset_x + j_maze * cell_size + cell_size/2
                        y = maze_offset_y + i_maze * cell_size + cell_size/2
                        fallback_positions.append((x, y))
            
            if len(fallback_positions) > 0:
                x, y = random.choice(fallback_positions)
                police_positions[i] = [x, y, 0]
                police_original_positions[i] = [x, y]
                li = [0, 90, 180, 270]
                police_directions[i] = random.choice(li)
                police_movement_timers[i] = 0  # Reset movement timer

def respawn_player():
    """Respawn the player at death position with random police placement"""
    global player_health, showing_respawn_message, level_timer_active, player_direction
    
    # Reset health and direction
    player_health = max_health
    player_direction = 0
    
    # Respawn player at death position
    player_pos[0] = death_position[0]
    player_pos[1] = death_position[1]
    player_pos[2] = death_position[2]
    
    # Respawn police randomly
    respawn_police_randomly()
    
    # Mark current position as visited
    update_visited_paths()
    
    # Resume game
    showing_respawn_message = False
    level_timer_active = True

def update_respawn_timer():
    """Update the respawn countdown timer"""
    global respawn_timer
    
    if showing_respawn_message and respawn_timer > 0:
        respawn_timer -= 1
        if respawn_timer <= 0:
            respawn_player()

def draw_visited_paths():
    """Draw yellow markers on visited paths"""
    if not visited_paths:
        return
    
    cell_size = WALL_THICKNESS * 2
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0)  # Yellow color for visited paths
    
    # Enable blending for semi-transparent effect
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 1.0, 0.0, 0.6)  # Semi-transparent yellow
    
    for grid_x, grid_y in visited_paths:
        # Calculate world position
        world_x = maze_offset_x + grid_x * cell_size + cell_size/2
        world_y = maze_offset_y + grid_y * cell_size + cell_size/2
        
        # Draw a yellow square on the floor
        glBegin(GL_QUADS)
        half_size = path_track_size
        glVertex3f(world_x - half_size, world_y - half_size, 2)
        glVertex3f(world_x + half_size, world_y - half_size, 2)
        glVertex3f(world_x + half_size, world_y + half_size, 2)
        glVertex3f(world_x - half_size, world_y + half_size, 2)
        glEnd()
    
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)

class Laser:
    """Laser security system with moving endpoints"""
    def __init__(self, x1, z1, x2, z2, movement_type='static'):
        # Convert 2D coordinates to 3D maze coordinates
        self.original_start = [x1, z1, 5]  # 5 units above ground
        self.original_end = [x2, z2, 5]
        self.start = [x1, z1, 5]  # Current position
        self.end = [x2, z2, 5]    # Current position
        self.active = True
        self.movement_type = movement_type
        self.movement_speed = 0.01  # Reduced from 0.02 for slower movement
        self.movement_time = 0
        self.movement_range = 100  # Movement range in maze units
    
    def update(self):
        """Update laser movement based on type"""
        if not self.active:
            return
            
        self.movement_time += self.movement_speed
        
        if self.movement_type == 'horizontal_fixed':
            # One end fixed, other moves horizontally
            offset = math.sin(self.movement_time) * self.movement_range
            self.start[0] = self.original_start[0]
            self.start[1] = self.original_start[1]
            self.end[0] = self.original_end[0]
            self.end[1] = self.original_end[1] + offset
            
        elif self.movement_type == 'vertical_fixed':
            # One end fixed, other moves vertically
            offset = math.sin(self.movement_time) * self.movement_range
            self.start[0] = self.original_start[0]
            self.start[1] = self.original_start[1]
            self.end[0] = self.original_end[0] + offset
            self.end[1] = self.original_end[1]
    
    def check_collision(self, player_x, player_y, player_z):
        """Check if player collides with laser beam - only when red line hits player body"""
        if not self.active:
            return False
        
        # Check if player is at laser height (around 5 units)
        # If player is jumping high enough, they should avoid lasers
        if player_z > 8:  # Lowered from 15 to 8 for more generous jumping
            return False
        
        # Calculate distance from player to laser line
        x1, y1 = self.start[0], self.start[1]
        x2, y2 = self.end[0], self.end[1]
        px, py = player_x, player_y
        
        # Check if player is within the laser segment bounds first (with small buffer)
        min_x = min(x1, x2) - 5
        max_x = max(x1, x2) + 5
        min_y = min(y1, y2) - 5
        max_y = max(y1, y2) + 5
        
        if not (px >= min_x and px <= max_x and py >= min_y and py <= max_y):
            return False
        
        # Line equation: Ax + By + C = 0
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        # Distance from point to line
        if A == 0 and B == 0:
            return False
            
        distance = abs(A * px + B * py + C) / math.sqrt(A * A + B * B)
        
        # Much more precise collision - only hit if very close to the actual laser line
        # Use player radius (8) to determine collision with laser beam
        return distance <= PLAYER_RADIUS  # Only hit if laser line intersects player body
    
    def draw(self):
        """Draw the laser beam and emitters"""
        if not self.active:
            return
        
        # Draw laser emitters at both ends
        for pos in [self.start, self.end]:
            glPushMatrix()
            glTranslatef(pos[0], pos[1], pos[2])
            glColor3f(*LASER_EMITTER_COLOR)
            glScalef(15, 15, 15)
            glutSolidCube(1.0)
            glPopMatrix()
        
        # Draw laser beam
        glDisable(GL_LIGHTING)
        glColor3f(*LASER_COLOR)
        glLineWidth(4.0)
        glBegin(GL_LINES)
        glVertex3f(self.start[0], self.start[1], self.start[2])
        glVertex3f(self.end[0], self.end[1], self.end[2])
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

def advance_level():
    """Advance to the next level after treasure collection"""
    global level, treasure_collected, level_complete, num_police
    global showing_level_message, level_message_timer, waiting_for_enter
    global near_treasure, near_door, showing_escape_message, waiting_for_next_level
    global player_pos, player_direction  # Add player position reset
    
    print(f"Advancing from level {level} to level {level + 1}")
    
    level += 1
    num_police += 1  # Increase number of police
    
    print(f"New level: {level}, Police count: {num_police}")
    
    # Reset game state
    treasure_collected = False
    level_complete = False
    near_treasure = False
    near_door = False
    showing_escape_message = False
    waiting_for_next_level = False
    
    # Reset player position to starting position
    player_direction = 0  # Reset player facing direction
    cell_size = WALL_THICKNESS * 2
    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j] == 0:
                player_pos[0] = maze_offset_x + j * cell_size + cell_size/2
                player_pos[1] = maze_offset_y + i * cell_size + cell_size/2
                player_pos[2] = 0
                break
        else:
            continue
        break
    
    print(f"Player reset to starting position: ({player_pos[0]:.1f}, {player_pos[1]:.1f}, {player_pos[2]:.1f})")
    
    # Clear visited paths for new level
    clear_visited_paths()
    
    # Initialize timer for new level
    init_level_timer()
    
    # Show level message without waiting for enter
    showing_level_message = True
    level_message_timer = 120  # Show for 120 frames (about 2 seconds)
    waiting_for_enter = False  # Don't wait for enter key press
    
    print(f"About to place game objects for level {level}")
    
    # Regenerate game objects
    place_game_objects()
    
    print(f"Level {level} setup complete")

def check_game_events():
    """Check for treasure collection and police encounters"""
    global treasure_collected, level_complete, game_over, player_health, near_treasure, near_door, showing_escape_message
    
    # Check if player is near treasure (for display purposes)
    if not treasure_collected:
        dist_to_treasure = math.sqrt(
            (player_pos[0] - treasure_pos[0])**2 +
            (player_pos[1] - treasure_pos[1])**2
        )
        near_treasure = dist_to_treasure < PLAYER_RADIUS + 30
    else:
        near_treasure = False
    
    # Check if player is near door (only after collecting treasure)
    if treasure_collected:
        dist_to_door = math.sqrt(
            (player_pos[0] - door_pos[0])**2 +
            (player_pos[1] - door_pos[1])**2
        )
        near_door = dist_to_door < PLAYER_RADIUS + 30
    else:
        near_door = False
    
    # Check police encounters (direct collision)
    if not (cheat_mode and god_mode):
        for police in police_positions:
            dist_to_police = math.sqrt(
                (player_pos[0] - police[0])**2 +
                (player_pos[1] - police[1])**2
            )
            if dist_to_police < PLAYER_RADIUS + POLICE_RADIUS:
                player_health -= 5  # Bigger damage for direct contact
                if player_health <= 0:
                    handle_player_death()
                break

def collect_treasure():
    """Collect treasure when player presses P near it"""
    global treasure_collected
    if near_treasure and not treasure_collected:
        treasure_collected = True

def escape_through_door():
    """Escape through door when player is near it after collecting treasure"""
    global showing_escape_message, waiting_for_next_level, level_complete
    if near_door and treasure_collected:
        showing_escape_message = True
        waiting_for_next_level = True
        level_complete = True

def keyboardListener(key, x, y):
    """Handle keyboard inputs"""
    global player_pos, player_direction, first_person_view, top_view, zoom_level, game_over, waiting_for_enter
    global w_key_pressed, space_key_pressed, waiting_for_next_level, showing_escape_message
   
    # Handle treasure collection with P key
    if key == b'p' or key == b'P':
        collect_treasure()
        if near_door and treasure_collected:
            escape_through_door()
    
    # Handle next level progression with N key
    if (key == b'n' or key == b'N') and waiting_for_next_level:
        print(f"N key pressed! waiting_for_next_level: {waiting_for_next_level}")
        waiting_for_next_level = False
        showing_escape_message = False
        advance_level()
    
    # Jump when Space is pressed (during normal gameplay)
    if key == b' ' and not game_over and not level_complete and not showing_respawn_message:
        space_key_pressed = True
        jump()
        # Don't return here - allow other key processing to continue
   
    # Reset the game if R is pressed during game over
    if key == b'r' and game_over:
        reset_game()
        return
   
    # Don't process other inputs during respawn message
    if showing_respawn_message:
        return
   
    # Cheat mode controls - only C key needed
    if key == b'c':
        toggle_cheat_mode()
        return
    
    # Camera view controls - allow these even during game over
    # Toggle views
    if key == b'v':
        if top_view:
            top_view = False
            first_person_view = True
        elif first_person_view:
            first_person_view = False
            top_view = False
        else:
            top_view = True
        update_camera()
        return
        
    # Toggle zoom
    if key == b'z' and not first_person_view and not top_view:
        zoom_level = max_zoom if zoom_level == 1.0 else 1.0
        update_camera()
        return
        
    # Top-down view
    if key == b't':
        top_view = True
        first_person_view = False
        update_camera()
        return
   
    if game_over or level_complete:
        return
   
    # Movement vectors
    forward_x = math.cos(math.radians(player_direction)) * player_speed
    forward_y = math.sin(math.radians(player_direction)) * player_speed
    right_x = math.cos(math.radians(player_direction - 90)) * player_speed
    right_y = math.sin(math.radians(player_direction - 90)) * player_speed
   
    # Movement controls
    if key == b'w':
        w_key_pressed = True
        # Normal forward movement (jumping provides automatic forward movement)
        movement_with_collision_detection(forward_x, forward_y)
    elif key == b's': movement_with_collision_detection(-forward_x, -forward_y)
    elif key == b'a': movement_with_collision_detection(-right_x, -right_y)
    elif key == b'd': movement_with_collision_detection(right_x, right_y)
    elif key == b'q': player_direction = (player_direction + 5) % 360
    elif key == b'e':
        player_direction = (player_direction - 5) % 360
   
    update_camera()

def keyboardUpListener(key, x, y):
    """Handle key release events"""
    global w_key_pressed, space_key_pressed
    
    if key == b'w':
        w_key_pressed = False
    elif key == b' ':
        space_key_pressed = False

def update_camera():
    """Update camera position based on view mode"""
    global camera_pos
   
    if top_view:
        maze_center_x = maze_offset_x + maze_width/2
        maze_center_y = maze_offset_y + maze_height/2
        camera_pos = (maze_center_x, maze_center_y, 800)
    elif first_person_view:
        eye_height = 70
        camera_pos = (player_pos[0], player_pos[1], player_pos[2] + eye_height)
    else:
        distance_behind = 200 * zoom_level
        height_above = 150 * zoom_level
        camera_angle = player_direction + 180
        dx = math.cos(math.radians(camera_angle)) * distance_behind
        dy = math.sin(math.radians(camera_angle)) * distance_behind
        camera_pos = (player_pos[0] + dx, player_pos[1] + dy, player_pos[2] + height_above)

def setupCamera():
    """Configure camera projection and view"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    if top_view:
        margin = max(maze_width, maze_height) * 0.6
        glOrtho(
            maze_offset_x - margin, 
            maze_offset_x + maze_width + margin,
            maze_offset_y - margin, 
            maze_offset_y + maze_height + margin,
            0.1, 2000
        )
    elif first_person_view:
        gluPerspective(70, 1.25, 0.1, 2000)
    else:
            gluPerspective(45, 1.25, 0.1, 2000)
   
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x, y, z = camera_pos
   
    if top_view:
        gluLookAt(x, y, z, x, y, 0, 0, 1, 0)
    elif first_person_view:
        look_x = player_pos[0] + math.cos(math.radians(player_direction)) * 10
        look_y = player_pos[1] + math.sin(math.radians(player_direction)) * 10
        look_z = player_pos[2] + 70
        gluLookAt(x, y, z, look_x, look_y, look_z, 0, 0, 1)
    else:
        gluLookAt(x, y, z, player_pos[0], player_pos[1], player_pos[2] + 40, 0, 0, 1)

def idle():
    """Idle function for continuous updates"""
    global level_message_timer, showing_level_message
    
    if showing_level_message:
        level_message_timer -= 1
        if level_message_timer <= 0:
            showing_level_message = False
    
    # Update respawn timer if showing respawn message
    if showing_respawn_message:
        update_respawn_timer()
    
    if not game_over and not showing_level_message and not showing_respawn_message:
        update_jump()  # Update jump physics
        move_police()
        check_police_detection() 
        update_lasers()
        check_laser_collision()
        check_game_events()
        update_timer()  # Update the level timer
    glutPostRedisplay()

def display():
    """Main display function"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setupCamera()
    update_lighting()
    draw_floor()
    draw_visited_paths()  # Draw visited paths before other objects
    draw_police_detection_zone() 
    draw_maze()
    draw_player()
    draw_police()
    draw_lasers()
    draw_treasure()
    draw_escape_door()  # Draw escape door
    draw_health_bar()
    draw_cheat_indicators()
    display_game_info()
    glutSwapBuffers()

def display_game_info():
    """Display game status information"""
    view_mode = "Top View" if top_view else "First Person" if first_person_view else "Third Person"
    
    # Handle respawn message display
    if showing_respawn_message:
        # Show respawn message in the center of the screen
        draw_text(400, 400, f"YOU HAVE {player_lives} LIVES LEFT", font_size='large', color=(1.0, 0.5, 0.0))
        remaining_seconds = (respawn_timer // 60) + 1
        draw_text(400, 350, f"RESPAWNING IN {remaining_seconds} SECONDS...", color=(1.0, 1.0, 0.0))
        return
    
    # Handle game over display
    if game_over:
        # Show the game over message in the center of the screen
        draw_text(400, 400, "GAME OVER", font_size='large', color=(1.0, 0.0, 0.0))
        
        # Check what caused the game over and display appropriate message
        if death_cause == "time":
            draw_text(400, 350, "TIME UP!", color=(1.0, 0.3, 0.3))
            draw_text(400, 320, "PRESS 'R' TO RESTART", color=(0.0, 1.0, 0.5))
        elif death_cause == "laser":
            draw_text(400, 350, "HIT THE LASER!", color=(1.0, 0.3, 0.3))
            draw_text(400, 320, "PRESS 'R' TO RESTART", color=(0.0, 1.0, 0.5))
        elif death_cause == "police":
            draw_text(400, 350, "CAUGHT BY POLICE!", color=(1.0, 0.3, 0.3))
            draw_text(400, 320, "PRESS 'R' TO RESTART", color=(0.0, 1.0, 0.5))
        else:
            # Fallback for any other case
            draw_text(400, 350, "ALL LIVES LOST!", color=(1.0, 0.3, 0.3))
            draw_text(400, 320, "PRESS 'R' TO RESTART", color=(0.0, 1.0, 0.5))
        return
    
    # Handle level up message
    elif showing_level_message:
        # Make text bigger and centered
        draw_text(400, 400, f"LEVEL {level}", font_size='large', color=(0.2, 0.8, 0.2))
        draw_text(400, 350, f"{num_police} POLICE OFFICERS HUNTING YOU!", color=(1.0, 0.5, 0.0))
        draw_text(400, 330, f"{len(lasers)} LASER SECURITY SYSTEMS ACTIVE!", color=(1.0, 0.0, 0.0))
        draw_text(400, 300, f"TIME LIMIT: {format_time(level_time_limit)}", color=(1.0, 1.0, 0.0))
        # Removed "PRESS ENTER TO CONTINUE" text - N key directly advances level
        return
        
    # Handle escape message display
    if showing_escape_message:
        draw_text(400, 400, f"YOU ESCAPED LEVEL {level}!", font_size='large', color=(0.0, 1.0, 0.0))
        draw_text(400, 350, "PRESS N TO GO TO NEXT LEVEL", color=(1.0, 1.0, 0.0))
        return
        
    # Regular game info display with interaction prompts
    if near_treasure and not treasure_collected:
        status = "Press P to collect treasure!"
        status_color = (1.0, 1.0, 0.0)  # Yellow
    elif not treasure_collected and near_door:
        status = "Collect the treasure first before using the door!"
        status_color = (1.0, 0.5, 0.0)  # Orange
    elif treasure_collected and not near_door:
        status = "Treasure collected! Find the blue door to escape!"
        status_color = (0.0, 1.0, 0.3)  # Green
    elif treasure_collected and near_door:
        status = "Press P to escape through the door!"
        status_color = (0.0, 0.8, 1.0)  # Cyan
    else:
        status = "Find the treasure and avoid the police!"
        status_color = (1.0, 1.0, 1.0)  # White

    # Draw status with special color
    draw_text(20, 750, status, color=status_color)
    
    # Draw health if not in god mode
    if not (cheat_mode and god_mode):
        health_color = (0.0, 1.0, 0.0) if player_health > 60 else (1.0, 1.0, 0.0) if player_health > 30 else (1.0, 0.0, 0.0)
        draw_text(20, 25, f"Health: {player_health}/{max_health}", color=health_color)
    
    # Draw lives counter (hide in cheat mode)
    if not cheat_mode:
        lives_color = (1.0, 1.0, 1.0) if player_lives > 1 else (1.0, 1.0, 0.0) if player_lives == 1 else (1.0, 1.0, 1.0)
        draw_text(20, 50, f"Lives: {player_lives}/{max_lives}", color=lives_color)
    
    # Draw timer
    timer_color = get_timer_color()
    draw_text(750, 750, f"Time: {format_time(level_time_remaining)}", color=timer_color)
    
    y_pos = 700
    # Draw level info with light blue
    draw_text(20, y_pos, f"Level: {level}", color=(1.0, 1.0, 1.0))
    y_pos -= 20
    
    # Draw lives count with light green
    draw_text(20, y_pos, f"Lives: {player_lives}", color=(1, 1.0, 1.5))
    y_pos -= 20

    # Draw view mode info with light purple
    draw_text(20, y_pos, f"View Mode: {view_mode}", color=(1.7, 1.5, 1.0))
    y_pos -= 20
    
    # Draw laser system status
    laser_status = "DISABLED" if (cheat_mode and laser_disabled) else "ACTIVE"
    laser_color = (0.5, 1.0, 0.5) if laser_disabled else (1.0, 0.3, 0.3)
    draw_text(20, y_pos, f"Lasers : {laser_status}", color=laser_color)

def reset_game():
    """Reset the game to initial state"""
    global player_pos, player_direction, game_over, treasure_collected, level_complete
    global police_positions, police_directions, police_original_positions, police_movement_timers
    global level, num_police, showing_level_message, waiting_for_enter
    global cheat_mode, god_mode, wall_walk_mode, player_health
    global player_lives, respawn_timer, showing_respawn_message, level_timer_active
    global near_treasure, near_door, showing_escape_message, waiting_for_next_level, death_cause
    
    # Reset game state
    game_over = False
    treasure_collected = False
    level_complete = False
    near_treasure = False
    death_cause = ""  # Reset death cause
    near_door = False
    showing_escape_message = False
    waiting_for_next_level = False
    showing_level_message = False
    waiting_for_enter = False
    showing_respawn_message = False
    respawn_timer = 0
    level_timer_active = True
    
    # Reset cheat modes
    cheat_mode = False
    god_mode = False
    wall_walk_mode = False
    laser_disabled = False  # Reset laser system
    player_health = max_health
    player_lives = max_lives  # Reset lives to 3
    
    # Reset jump system
    global is_jumping, jump_velocity
    is_jumping = False
    jump_velocity = 0.0
    
    # Reset to level 1
    level = 1
    num_police = 2  # Initial number of police
    
    # Clear visited paths
    clear_visited_paths()
    
    # Initialize timer for level 1
    init_level_timer()
    
    # Initialize police movement timers
    police_movement_timers = []
    
    # Reset player position and orientation to the starting position (1,1)
    player_direction = 0  # Reset player facing direction
    cell_size = WALL_THICKNESS * 2
    
    # Set player to the starting position (row 1, col 1 - first open cell)
    start_row = 1
    start_col = 1
    player_pos[0] = maze_offset_x + start_col * cell_size + cell_size/2
    player_pos[1] = maze_offset_y + start_row * cell_size + cell_size/2
    player_pos[2] = 0
    
    print(f"Player reset to starting position: ({player_pos[0]:.1f}, {player_pos[1]:.1f}, {player_pos[2]:.1f})")
    
    # Mark starting position as visited
    update_visited_paths()
    
    # Regenerate game objects
    place_game_objects()
    update_camera()

def init():
    """Initialize the game"""
    global player_health, player_lives
    glClearColor(0.2, 0.2, 0.2, 1.0)  # Dark grey background
    init_3d()
    player_health = max_health  # Initialize player health
    player_lives = max_lives    # Initialize player lives
    
    # Initialize timer for level 1
    init_level_timer()

    # Find starting position
    cell_size = WALL_THICKNESS * 2
    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j] == 0:
                player_pos[0] = maze_offset_x + j * cell_size + cell_size/2
                player_pos[1] = maze_offset_y + i * cell_size + cell_size/2
                player_pos[2] = 0
                # Mark starting position as visited
                update_visited_paths()
                return
    
    player_pos[0] = 0
    player_pos[1] = 0
    player_pos[2] = 0

def main():
    """Main function"""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Treasure Robbery Game - Enhanced with Cheat Mode")
    
    init()
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(lambda *args: None)
    glutMouseFunc(lambda *args: None)
    
    update_camera()
    glutMainLoop()

if __name__ == "__main__":
    main()
