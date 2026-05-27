LEVELS = {
    1: {
        'name': 'Destroyed City',
        'boss_name': 'Titan Drone',
        'boss_hp': 80,
        'boss_image': 'boss_city',

        'bg_top': (10, 10, 25),
        'bg_bottom': (35, 35, 60),

        'star_color': (180, 180, 255),
        'particle_color': (255, 120, 50),

        'menu_color': (40, 60, 120),

        'block_color': (241, 79, 80),

        'alien_colors': ['red', 'green', 'yellow'],

        'enemy_laser_color': (255, 80, 80),

        'alien_speed': 1,
        'rows': 5,
        'cols': 10,

        'boss_color': (255, 80, 80),
        'boss_speed': 2,
        'boss_pattern': 'horizontal',

        'layout': 'city'
    },

    2: {
        'name': 'Toxic Forest',
        'boss_name': 'Mutant Tree',
        'boss_hp': 130,
        'boss_image': 'boss_forest',

        'bg_top': (5, 30, 10),
        'bg_bottom': (15, 70, 30),

        'star_color': (120, 255, 120),
        'particle_color': (120, 255, 80),

        'menu_color': (40, 120, 60),

        'block_color': (80, 220, 120),

        'alien_colors': ['green', 'yellow', 'red'],

        'enemy_laser_color': (100, 255, 100),

        'alien_speed': 2,
        'rows': 6,
        'cols': 9,

        'boss_color': (80, 255, 120),
        'boss_speed': 4,
        'boss_pattern': 'wave',

        'layout': 'forest'
    },

    3: {
        'name': 'AI Core',
        'boss_name': 'Central AI',
        'boss_hp': 180,
        'boss_image': 'boss_ai',

        'bg_top': (15, 5, 25),
        'bg_bottom': (80, 20, 45),

        'star_color': (255, 120, 255),
        'particle_color': (255, 50, 150),

        'menu_color': (120, 40, 80),

        'block_color': (200, 120, 255),

        'alien_colors': ['yellow', 'red', 'green'],

        'enemy_laser_color': (255, 50, 200),

        'alien_speed': 3,
        'rows': 4,
        'cols': 12,

        'boss_color': (255, 50, 200),
        'boss_speed': 5,
        'boss_pattern': 'aggressive',

        'layout': 'ai_core'
    }
}