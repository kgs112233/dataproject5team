import pandas as pd
import re
from google.cloud import language_v1
import os

GENRE_FACTORS = {
    "Action": {
        "Combat": {
            "SUCCESS": [r'fluid', r'fast-paced', r'responsive', r'satisfying', r'impact', r'smooth', r'precision', r'tight controls', r'combat is great'],
            "FAILURE": [r'clunky', r'slow', r'unresponsive', r'janky', r'awkward', r'hitbox', r'spam', r'repetitive', r'bad controls', r'feels stiff', r'no impact']
        },
        "Controls": {
            "SUCCESS": [r'precision', r'tight controls', r'responsive', r'smooth movement', r'quick reaction'],
            "FAILURE": [r'unresponsive controls', r'laggy', r'input delay', r'clunky movement', r'awkward controls', r'bad hit registration']
        },
        "Difficulty": {
            "SUCCESS": [r'challenging but fair', r'satisfying difficulty', r'great challenge', r'good balancing', r'hard but rewarding'],
            "FAILURE": [r'too easy', r'too hard', r'unfair difficulty', r'poorly balanced', r'frustrating difficulty', r'spikes in difficulty']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "Strategy": {
        "StrategicVariety": {
            "SUCCESS": [r'strategic depth', r'diverse strategies', r'many ways to win', r'flexible tactics', r'complex decisions'],
            "FAILURE": [r'single strategy', r'one dominant path', r'boring choices', r'linear tactics', r'lack of depth']
        },
        "AIQuality": {
            "SUCCESS": [r'smart AI', r'challenging AI', r'clever opponent', r'AI is competitive'],
            "FAILURE": [r'dumb AI', r'stupid AI', r'AI cheats', r'predictable AI', r'no challenge from AI']
        },
        "InfoClarity": {
            "SUCCESS": [r'clear information', r'good feedback', r'intuitive interface', r'easy to understand data'],
            "FAILURE": [r'confusing data', r'unclear information', r'bad feedback', r'obscure mechanics', r'hard to read UI']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "Indie": {
        "Originality": {
            "SUCCESS": [r'innovative', r'unique concept', r'original idea', r'fresh take', r'unseen'],
            "FAILURE": [r'generic', r'unoriginal', r'copied formula', r'stale concept']
        },
        "Polish/Bugs": {
            "SUCCESS": [r'highly polished', r'no crashes', r'stable performance', r'smooth experience', r'no bugs'],
            "FAILURE": [r'buggy', r'crashes constantly', r'technical issues', r'poor optimization', r'glitches', r'unstable']
        },
        "Value": {
            "SUCCESS": [r'great value for money', r'worth the price', r'cheap but amazing', r'huge amount of content'],
            "FAILURE": [r'overpriced', r'not worth the money', r'too short for price', r'lack of content']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "RPG": {
        "Worldbuilding": {
            "SUCCESS": [r'rich world', r'deep lore', r'immersive setting', r'believable world', r'compelling atmosphere'],
            "FAILURE": [r'bland world', r'weak lore', r'generic setting', r'inconsistent worldbuilding']
        },
        "Rewards": {
            "SUCCESS": [r'satisfying progression', r'meaningful rewards', r'great loot', r'rewarding choices', r'feel powerful'],
            "FAILURE": [r'grindy', r'boring leveling', r'weak rewards', r'no excitement from loot', r'pointless progression']
        },
        "Freedom/Choice": {
            "SUCCESS": [r'high freedom', r'many choices', r'impactful decisions', r'multiple paths', r'open-ended'],
            "FAILURE": [r'linear path', r'no real choice', r'decisions dont matter', r'railroading', r'low freedom']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "Simulation": {
        "SystemDepth": {
            "SUCCESS": [r'deep mechanics', r'complex systems', r'robust simulation', r'high fidelity', r'lots of detail'],
            "FAILURE": [r'shallow system', r'simplistic mechanics', r'no depth', r'fake depth', r'too easy']
        },
        "UI/Interface": {
            "SUCCESS": [r'intuitive UI', r'easy to navigate', r'clear interface', r'user-friendly', r'clean design'],
            "FAILURE": [r'clunky UI', r'confusing menus', r'bad interface', r'poor readability', r'unnecessary clicking']
        },
        "Realism": {
            "SUCCESS": [r'highly realistic', r'accurate simulation', r'authentic feel', r'true to life physics'],
            "FAILURE": [r'unrealistic', r'bad physics', r'feels arcadey', r'poor implementation of reality']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "Adventure": {
        "Story": {
            "SUCCESS": [r'engaging story', r'well-written narrative', r'emotional plot', r'memorable characters', r'great plot'],
            "FAILURE": [r'weak story', r'plotholes', r'boring plot', r'bad writing', r'narrative falls apart']
        },
        "Exploration": {
            "SUCCESS": [r'satisfying exploration', r'strong exploration motive', r'rich world', r'fun to explore', r'discovery'],
            "FAILURE": [r'monotonous exploration', r'linear map', r'empty world', r'no reason to explore', r'tedious backtracking']
        },
        "Atmosphere": {
            "SUCCESS": [r'immersive atmosphere', r'stunning visuals', r'great sound design', r'world-building is excellent', r'mood'],
            "FAILURE": [r'dull atmosphere', r'generic setting', r'bad sound', r'not immersive', r'lack of mood']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "Casual": {
        "Addictiveness": {
            "SUCCESS": [r'highly addictive', r'hard to put down', r'just one more round', r'compulsive gameplay', r'endless fun'],
            "FAILURE": [r'gets boring fast', r'no replay value', r'easily bored', r'repetitive gameplay']
        },
        "Variety/LevelDesign": {
            "SUCCESS": [r'diverse levels', r'high variety', r'creative stages', r'many mini-games', r'simple controls yet deep'],
            "FAILURE": [r'repetitive levels', r'low variety', r'too many similar stages', r'lack of innovation', r'too simple controls']
        },
        "Playtime/Pacing": {
            "SUCCESS": [r'perfect playtime', r'satisfying length', r'good pacing', r'easy to pick up and play'],
            "FAILURE": [r'too short', r'too long', r'bad pacing', r'feels like a chore', r'time commitment is high']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
    "Puzzle": {
        "Logic/Intuition": {
            "SUCCESS": [r'logical puzzles', r'intuitive solutions', r'clear rules', r'well-designed puzzles', r'makes sense'],
            "FAILURE": [r'illogical puzzles', r'unreasonable solutions', r'guesswork puzzles', r'makes no sense', r'frustrating puzzle']
        },
        "DifficultyCurve": {
            "SUCCESS": [r'smooth difficulty curve', r'natural progression', r'ramps up perfectly', r'fair challenges'],
            "FAILURE": [r'erratic difficulty', r'sudden spikes', r'badly balanced puzzles', r'too easy then too hard']
        },
        "Novelty": {
            "SUCCESS": [r'novel puzzle mechanics', r'creative elements', r'fresh ideas', r'never seen before', r'innovative puzzles'],
            "FAILURE": [r'generic puzzles', r'reused mechanics', r'stale puzzles', r'too simple', r'unoriginal elements']
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    
}

NEW_GENRE_FACTORS = {
    'Racing': {
        'Vehicle Handling': {
            'SUCCESS': [
                r'natural handling',
                r'car control(s)? feel(s)? natural',
                r'smooth steering',
                r'responsive steering',
                r'responsive control(s)?',
                r'feel(s)? good to drive',
                r'good handling model',
                r'precise steering',
                r'tight handling',
                r'easy to control the car',
            ],
            'FAILURE': [
                r'awkward handling',
                r'car control(s)? feel(s)? awkward',
                r'floaty handling',
                r'floaty steering',
                r'unresponsive steering',
                r'unresponsive control(s)?',
                r'sloppy handling',
                r'weird handling model',
                r'too sensitive steering',
                r'hard to control the car',
            ],
        },
        'Track Variety': {
            'SUCCESS': [
                r'many track(s)?',
                r'lots of track(s)?',
                r'diverse track(s)?',
                r'varied course(s)?',
                r'plenty of circuit(s)?',
                r'different environment(s)? to race',
                r'good track variety',
                r'wide variety of race track(s)?',
            ],
            'FAILURE': [
                r'repetitive track(s)?',
                r'same track(s)? over and over',
                r'low track variety',
                r'lack(s)? track variety',
                r'few track(s)?',
                r'only a handful of track(s)?',
                r'boring track design',
                r'monotonous course(s)?',
            ],
        },
        'Graphics & Immersion': {
            'SUCCESS': [
                r'great graphic(s)?',
                r'graphic(s)? look(s)? great',
                r'visual(s)? enhance immersion',
                r'graphic(s)? fit the game',
                r'visual style fit(s)? the game',
                r'immersive visual(s)?',
                r'detailed car model(s)?',
                r'beautiful environment(s)?',
                r'good lighting',
                r'graphics help immersion',
            ],
            'FAILURE': [
                r'graphic(s)? don\'t fit the game',
                r'visual(s)? don\'t match the tone',
                r'poor graphic(s)?',
                r'low fidelity graphic(s)?',
                r'ugly visual(s)?',
                r'outdated graphic(s)?',
                r'graphic(s)? break immersion',
                r'lack(s)? detail in car model(s)?',
                r'bad texture(s)? on track(s)?',
            ],
        },
        'Vehicle Variety': {
            'SUCCESS': [
                r'many car(s)? to choose',
                r'large car roster',
                r'wide variety of vehicle(s)?',
                r'diverse car selection',
                r'lots of vehicle type(s)?',
                r'plenty of car(s)? to unlock',
                r'good car variety',
            ],
            'FAILURE': [
                r'few car(s)? to choose',
                r'limited car selection',
                r'lack(s)? vehicle variety',
                r'very few vehicle(s)?',
                r'same car(s)? all the time',
                r'not enough car(s)?',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    'JRPG': {
        'Character Appeal': {
            'SUCCESS': [
                r'memorable character(s)?',
                r'strong character personality',
                r'great cast of character(s)?',
                r'likable character(s)?',
                r'well written character(s)?',
                r'character(s)? stand out',
                r'distinct party member(s)?',
                r'good character dynamic(s)?',
            ],
            'FAILURE': [
                r'bland character(s)?',
                r'flat character(s)?',
                r'boring cast',
                r'forgettable character(s)?',
                r'no personality in character(s)?',
                r'generic party member(s)?',
                r'weak character writing',
            ],
        },
        'World Atmosphere': {
            'SUCCESS': [
                r'rich worldbuilding',
                r'rich world building',
                r'great atmosphere',
                r'evocative setting',
                r'strong sense of world',
                r'immersive world',
                r'world feel(s)? alive',
                r'unique jrpg world',
                r'beautiful fantasy world',
            ],
            'FAILURE': [
                r'weak worldbuilding',
                r'weak world building',
                r'shallow setting',
                r'hard to get into the world',
                r'world feel(s)? empty',
                r'world feel(s)? generic',
                r'low immersion in the world',
                r'uninspired setting',
            ],
        },
        'Level Flow & Fatigue': {
            'SUCCESS': [
                r'good dungeon design',
                r'well designed dungeon(s)?',
                r'good level design',
                r'flow(s)? well',
                r'not too much backtracking',
                r'minimal backtracking',
                r'good pacing in dungeon(s)?',
                r'doesn\'t feel tedious',
                r'not too grindy to progress',
            ],
            'FAILURE': [
                r'bad dungeon design',
                r'poor level design',
                r'confusing dungeon layout',
                r'too much backtracking',
                r'constant backtracking',
                r'tedious dungeon(s)?',
                r'layout cause(s)? fatigue',
                r'level design break(s)? immersion',
                r'too grindy to progress',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    'Massively Multiplayer': {
        'Content Volume': {
            'SUCCESS': [
                r'lots of content',
                r'tons of content',
                r'a lot of thing(s)? to do',
                r'content rich',
                r'plenty of dungeon(s)? and raid(s)?',
                r'many activity(ies)? available',
                r'varied endgame content',
                r'never run out of thing(s)? to do',
            ],
            'FAILURE': [
                r'lack(s)? content',
                r'content light',
                r'not enough content',
                r'run out of thing(s)? to do',
                r'nothing to do at endgame',
                r'shallow endgame',
                r'repetitive content only',
            ],
        },
        'Service Stability': {
            'SUCCESS': [
                r'stable server(s)?',
                r'server(s)? are stable',
                r'rarely disconnect(s)?',
                r'few disconnect(s)?',
                r'good uptime',
                r'stable service',
                r'no major server issue(s)?',
                r'smooth online experience',
            ],
            'FAILURE': [
                r'server issue(s)?',
                r'server(s)? unstable',
                r'constant disconnect(s)?',
                r'frequent disconnect(s)?',
                r'server downtime',
                r'can\'t log in',
                r'login issue(s)?',
                r'laggy server(s)?',
                r'poor server stability',
            ],
        },
    },

    'Tower Defense': {
        'Information Display': {
            'SUCCESS': [
                r'clear range indicator(s)?',
                r'good range indicator(s)?',
                r'wave info is clear',
                r'clear wave information',
                r'stats are easy to read',
                r'intuitive ui for tower info',
                r'good tooltip(s)? for tower(s)?',
                r'can easily see enemy path',
            ],
            'FAILURE': [
                r'no range indicator',
                r'lack(s)? range indicator(s)?',
                r'unclear wave info',
                r'wave information missing',
                r'stats are hard to read',
                r'confusing tower info',
                r'poor tooltip(s)?',
                r'unclear enemy path',
            ],
        },
        'Strategic Options': {
            'SUCCESS': [
                r'many tower type(s)?',
                r'varied tower(s)?',
                r'diverse strategy(ies)?',
                r'multiple viable build(s)?',
                r'many way(s)? to defend',
                r'high strategic depth',
                r'lots of upgrade path(s)?',
                r'good variety of tower upgrade(s)?',
            ],
            'FAILURE': [
                r'only one viable strategy',
                r'one strategy only',
                r'lack(s)? strategic depth',
                r'few tower type(s)?',
                r'limited tower choice(s)?',
                r'only one build work(s)?',
                r'repetitive strategy',
                r'not enough upgrade path(s)?',
            ],
        },
        'Accessibility & Engagement': {
            'SUCCESS': [
                r'easy to pick up',
                r'accessible for beginner(s)?',
                r'intuitive mechanic(s)?',
                r'good tutorial',
                r'quick to understand',
                r'gets you hooked quickly',
                r'immersive tower defense',
                r'keeps you engaged',
            ],
            'FAILURE': [
                r'hard to understand',
                r'confusing for beginner(s)?',
                r'bad tutorial',
                r'no tutorial',
                r'steep learning curve',
                r'can\'t get into it',
                r'fails to hook me',
                r'not engaging',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    'City Builder': {
        'Freedom & Map Scale': {
            'SUCCESS': [
                r'large map(s)?',
                r'huge map(s)?',
                r'big city area',
                r'lots of space to build',
                r'high freedom to build',
                r'build anywhere',
                r'open ended city builder',
                r'good building freedom',
            ],
            'FAILURE': [
                r'small map(s)?',
                r'tiny map(s)?',
                r'not enough space to build',
                r'low building freedom',
                r'strict building limit(s)?',
                r'can\'t expand the city',
                r'cramped city layout',
            ],
        },
        'Simulation Depth': {
            'SUCCESS': [
                r'deep simulation',
                r'complex city system(s)?',
                r'interconnected system(s)?',
                r'realistic simulation',
                r'many interacting mechanic(s)?',
                r'detail city management',
                r'satisfying city simulation',
            ],
            'FAILURE': [
                r'shallow simulation',
                r'simple city system(s)?',
                r'hollow mechanic(s)?',
                r'lack(s)? depth in system(s)?',
                r'too basic simulation',
                r'limited system interaction',
                r'oversimplified city model',
            ],
        },
        'City UI Usability': {
            'SUCCESS': [
                r'intuitive ui',
                r'clean interface',
                r'easy to use interface',
                r'ui is easy to navigate',
                r'good overlay(s)? for data',
                r'clear information display',
                r'building menu(s)? are simple',
            ],
            'FAILURE': [
                r'clunky ui',
                r'bad interface',
                r'ui is confusing',
                r'ui hard to navigate',
                r'poor overlay(s)?',
                r'hard to read city data',
                r'overly complex interface',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    'Metroidvania': {
        'Map Connectivity': {
            'SUCCESS': [
                r'excellent map design',
                r'great map layout',
                r'interconnected map',
                r'shortcut(s)? feel rewarding',
                r'backtracking feel(s)? smart',
                r'fun to explore the map',
                r'satisfying level layout',
                r'map encourage(s)? exploration',
            ],
            'FAILURE': [
                r'confusing map layout',
                r'hard to navigate the map',
                r'get lost too easily',
                r'no sense of direction',
                r'too linear map',
                r'overly simple layout',
                r'boring corridor(s)?',
                r'bad map design',
            ],
        },
        'Ability Unlock Impact': {
            'SUCCESS': [
                r'new ability(ies)? change(s)? gameplay',
                r'ability unlock(s)? open new path(s)?',
                r'fun movement upgrade(s)?',
                r'great sense of progression',
                r'power(s)? feel meaningful',
                r'ability(ies)? add variety',
                r'creative use of power(s)?',
            ],
            'FAILURE': [
                r'ability unlock(s)? feel pointless',
                r'new ability(ies)? don\'t change much',
                r'power(s)? feel boring',
                r'upgrade(s)? are trivial',
                r'no real change in gameplay',
                r'ability(ies)? feel redundant',
                r'ability system is shallow',
            ],
        },
        'Boss Battles': {
            'SUCCESS': [
                r'memorable boss fight(s)?',
                r'great boss design',
                r'epic boss battle(s)?',
                r'satisfying boss pattern(s)?',
                r'boss fight(s)? feel fair',
                r'fun boss mechanic(s)?',
                r'boss(es)? are highlight(s)?',
            ],
            'FAILURE': [
                r'boring boss fight(s)?',
                r'generic boss(es)?',
                r'disappointing boss battle(s)?',
                r'forgettable boss(es)?',
                r'weak boss design',
                r'bad boss pattern(s)?',
                r'boss fight(s)? feel cheap',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    'Fighting': {
        'Hit Feel & Flow': {
            'SUCCESS': [
                r'great hit impact',
                r'hit(s)? feel satisfying',
                r'good hitstop',
                r'responsive combat flow',
                r'natural fight flow',
                r'animation(s)? feel weighty',
                r'combat feel(s)? smooth',
                r'punch(es)? feel heavy',
                r'good feedback on hit(s)?',
            ],
            'FAILURE': [
                r'weak hit impact',
                r'hit(s)? feel floaty',
                r'no weight to hit(s)?',
                r'combat feel(s)? stiff',
                r'combat feel(s)? clunky',
                r'fight flow is awkward',
                r'bad hit feedback',
                r'animation(s)? feel off',
            ],
        },
        'Character Balance': {
            'SUCCESS': [
                r'good character balance',
                r'well balanced roster',
                r'most character(s)? are viable',
                r'no clearly overpowered character',
                r'fair matchup(s)? overall',
                r'balanced cast',
            ],
            'FAILURE': [
                r'only one top tier character',
                r'only few viable character(s)?',
                r'one character dominate(s)?',
                r'overpowered character(s)?',
                r'unbalanced roster',
                r'character balance is bad',
                r'broken character(s)?',
            ],
        },
        'Combo Depth': {
            'SUCCESS': [
                r'deep combo system',
                r'lots of combo route(s)?',
                r'many combo option(s)?',
                r'creative combo(s)? possible',
                r'combo(s)? allow expression',
                r'varied combo route(s)?',
                r'complex combo mechanic(s)?',
            ],
            'FAILURE': [
                r'limited combo system',
                r'very few combo(s)?',
                r'only basic combo(s)?',
                r'no real combo depth',
                r'repetitive combo(s)?',
                r'same combo(s)? every time',
                r'combo system feel(s)? shallow',
            ],
        },
        'Online Infrastructure': {
            'SUCCESS': [
                r'stable netcode',
                r'rollback netcode work(s)? well',
                r'low latency online match(es)?',
                r'online play is smooth',
                r'no major lag online',
                r'good matchmaking',
                r'fair online environment',
            ],
            'FAILURE': [
                r'bad netcode',
                r'input delay online',
                r'laggy online match(es)?',
                r'rollback doesn\'t work',
                r'online play is unplayable',
                r'connection issue(s)? all the time',
                r'server latency problem(s)?',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },

    '4X': {
        'AI Behavior': {
            'SUCCESS': [
                r'smart ai',
                r'competent ai',
                r'ai play(s)? strategically',
                r'ai make(s)? good decision(s)?',
                r'challenging ai opponent(s)?',
                r'ai use(s)? diplomacy well',
                r'ai handle(s)? warfare well',
            ],
            'FAILURE': [
                r'dumb ai',
                r'stupid ai',
                r'ai is too passive',
                r'ai make(s)? nonsense decision(s)?',
                r'ai can be easily exploited',
                r'ai doesn\'t understand diplomacy',
                r'ai doesn\'t know how to wage war',
            ],
        },
        'Session Depth': {
            'SUCCESS': [
                r'deep campaign',
                r'long and satisfying session(s)?',
                r'complex late game',
                r'session(s)? stay interesting',
                r'deep mid game',
                r'lots of long term decision(s)?',
                r'rewarding long play session(s)?',
            ],
            'FAILURE': [
                r'session(s)? feel shallow',
                r'run out of depth quickly',
                r'late game is boring',
                r'mid game fall(s)? flat',
                r'no long term depth',
                r'game end(s)? before it get(s)? deep',
            ],
        },
        'Accessibility & Depth': {
            'SUCCESS': [
                r'accessible 4x',
                r'easy to learn but hard to master',
                r'good tutorial for system(s)?',
                r'ui help(s)? understanding mechanic(s)?',
                r'clear explanation of rule(s)?',
                r'gradual introduction of system(s)?',
            ],
            'FAILURE': [
                r'steep learning curve',
                r'overwhelming for beginner(s)?',
                r'no proper tutorial',
                r'unclear rule(s)?',
                r'poor explanation of system(s)?',
                r'hard to get into the game',
            ],
        },
        "TechIssues": {
            "SUCCESS": [
                r'no bugs',
                r'no lag',
                r'stable performance',
                r'well optimized',
                r'no crashes'
            ],
            "FAILURE": [
                r'\bbug(s)?\b',
                r'\bglitch(es)?\b',
                r'\bcrash(ed|es|ing)?\b',
                r'\blag(gy)?\b',
                r'\b(stutter|stuttering)\b',
                r'\bfps drop(s)?\b',
                r'\bframe drop(s)?\b',
                r'performance issue(s)?',
                r'poor(ly)? optimized',
                r'\boptimization\b',
                r'server issue(s)?',
                r'\bdisconnect(ed|s|ing)?\b',
                r'\bdesync\b',
                r'cheat(s|er|ers|ing)?',
                r'hack(er|ers|ing|s)?',
                r'exploit(s|ed|ing)?',
                r'\berror(s)?\b'
            ]
        },
        "Balance": {
            "SUCCESS": [
                r'well balanced',
                r'good balance',
                r'balanced gameplay',
                r'fair balance',
                r'balanced (classes|weapons|heroes)'
            ],
            "FAILURE": [
                r'bad balance',
                r'unbalanced',
                r'imbalanced',
                r'broken (class|weapon|build|character)',
                r'overpowered',
                r'\bOP\b',
                r'underpowered',
                r'needs nerf',
                r'needs buff',
                r'pay to win',
                r'\bp2w\b'
            ]
        },
        "Blame": {
            "SUCCESS": [

                r'devs listened',
                r'devs care',
                r'developers fixed it',
                r'great support from devs'
            ],
            "FAILURE": [

                r'lazy devs?',
                r'greedy devs?',
                r'devs? don\'t care',
                r'developers? don\'t care',
                r'terrible devs?',
                r'devs? ignored',
                r'devs? abandoned',
                r'cash grab',
                r'money grab',
                r'shameless cash grab',
                r'scam',

                r'predatory monetization',
                r'predatory microtransactions',
                r'paywall',

                r'toxic community',
                r'toxic players',
                r'worst community',
                r'shameful community'
            ]
        }
    },
        "Platformer": {
        "Control": {
            "SUCCESS": [
                r"precise(ly)? controls?", r"tight controls?", r"responsiv(e|ness)", r"smooth(ly)? (movement|gameplay)", 
                r"fluid(ity)?", r"snappy controls?", r"good handling", r"pixel perfect", r"sharp controls?", 
                r"accurate movement", r"perfect controls?", r"feels? good to play", r"intuitive controls?", r"no input lag"
            ],
            "FAILURE": [
                r"clunky(ness)?", r"slippery (controls?|movement)", r"floaty (physics|jump|controls?)", r"input (lag|delay|eating)",
                r"unresponsiv(e|ness)", r"slide around", r"janky controls?", r"stiff controls?", r"drift", 
                r"bad collision", r"imprecise", r"delayed jump", r"physics? (is|are) bad", r"wrestling with controls?"
            ]
        },
        "Level Design": {
            "SUCCESS": [
                r"creative(ly)? designed?", r"genius level design", r"well designed levels?", r"unique mechanics?", 
                r"smart (layout|placement)", r"fresh ideas?", r"good pacing", r"clever puzzle", r"shortcuts?", 
                r"hidden secrets?", r"interconnected world", r"great map design", r"verticality"
            ],
            "FAILURE": [
                r"repetitive (levels?|design)", r"boring levels?", r"tedious", r"frustrating design", r"bad(ly)? designed?",
                r"cheap (deaths?|placement)", r"confusing layout", r"maze", r"backtracking", r"samey", 
                r"linear levels?", r"empty levels?", r"copy paste", r"uninspired"
            ]
        },
        "Difficulty": {
            "SUCCESS": [
                r"challenging but fair", r"fair difficulty", r"satisfying challenge", r"hard but fair", r"good difficulty curve",
                r"rewarding", r"tough but fun", r"skill based", r"git gud", r"learning curve", r"requires skill"
            ],
            "FAILURE": [
                r"unfair(ly)?", r"impossible difficulty", r"rage inducing", r"annoying(ly)? hard", r"difficulty spike",
                r"unbalan(ced|ce)", r"artificial difficulty", r"cheap shots?", r"trial and error", r"punishing(ly)?",
                r"frustrating(ly)? hard", r"rng based difficulty"
            ]
        }
    },

    # 2. Horror (공포)
    "Horror": {
        "Atmosphere": {
            "SUCCESS": [
                r"scary atmosphere", r"terrify(ing|ed)?", r"tensi(on|ve)", r"immersi(ve|on)", r"creepy vibe",
                r"sense of dread", r"chilling", r"eerie", r"great atmosphere", r"unsettling", r"disturbing",
                r"psychological horror", r"claustrophobic", r"haunting", r"suspense(ful)?"
            ],
            "FAILURE": [
                r"not scary", r"boring", r"walking sim(ulator)?", r"not horror", r"ruins? the atmosphere",
                r"predictable", r"comed(y|ic)", r"not frightening", r"childish", r"lame", r"tried too hard"
            ]
        },
        "Jumpscare": {
            "SUCCESS": [
                r"well placed jumpscares?", r"good build up", r"tensi(on|ve) build", r"genuinely scary", r"frightening",
                r"caught me off guard", r"good scares?", r"heart racing", r"made me jump"
            ],
            "FAILURE": [
                r"cheap jumpscares?", r"loud noises?", r"annoying jumpscares?", r"jumpscare spam", r"predictable scares?",
                r"rel(ies|y) on jumpscares", r"screamers?", r"startle", r"ear rape", r"overuse of jumpscares?"
            ]
        },
        "Presentation": {
            "SUCCESS": [
                r"sound design", r"audio (is )?good", r"visuals? (are )?great", r"lighting (is )?good", r"good graphics?",
                r"art style", r"environment(al)? storytelling", r"detailed textures?", r"soundtrack", r"ambien(ce|t)"
            ],
            "FAILURE": [
                r"glitch(y|es)?", r"bug(s|gy)?", r"bad sound", r"poor(ly)? audio", r"bad graphics?", r"ugly textures?",
                r"looks? bad", r"clipping", r"low res", r"bad optimization", r"janky animations?", r"looks outdated"
            ]
        }
    },

    # 3. Shooter (FPS/TPS)
    "Shooter": {
        "Optimization": {
            "SUCCESS": [
                r"well optimiz(ed|ation)", r"runs? (smooth(ly)?|well)", r"high fps", r"stable (fps|performance)",
                r"good performance", r"solid framerate", r"no lag", r"butter(y)? smooth"
            ],
            "FAILURE": [
                r"poor(ly)? optimiz(ed|ation)", r"unoptimiz(ed|ation)", r"fps drops?", r"frame drops?", r"stutter(s|ing)?",
                r"crash(es|ing)?", r"freez(es|ing)?", r"lag(gy)?", r"memory leak", r"bad performance", r"low fps", r"rubber band(ing)?"
            ]
        },
        "Cheaters": {
            "SUCCESS": [
                r"good anticheat", r"clean (lobbies|games)", r"ban waves?", r"fair play", r"no cheaters?", r"cheater free"
            ],
            "FAILURE": [
                r"hacker(s|ing)?", r"cheater(s|ing)?", r"aimbot(s)?", r"wallhack(s)?", r"infested with (hackers|cheaters)",
                r"script(ers|ing)?", r"spinbot", r"hack vs hack", r"no anticheat", r"report system sucks?"
            ]
        },
        "Gunplay": {
            "SUCCESS": [
                r"satisfying gunplay", r"good (hit reg|registration)", r"balanced? (weapons|guns|classes)", r"feel(s)? good",
                r"snappy aiming", r"impactful", r"weapon variety", r"good recoil", r"sound design", r"ballistics?"
            ],
            "FAILURE": [
                r"broken (weapons?|guns?)", r"op weapons?", r"imbalan(ce|ced)", r"bullet spong(e|es)", r"bad hit reg",
                r"weak sounds?", r"peashooter", r"clunky aiming", r"bad recoil", r"meta slave", r"nerf(ed)?"
            ]
        }
    },

    # 4. Survival (생존)
    "Survival": {
        "Resource": {
            "SUCCESS": [
                r"crafting system", r"base building", r"realis(tic|m)", r"resource management", r"gathering is fun",
                r"survival mechanics?", r"scavenging", r"loot(ing)?", r"economy"
            ],
            "FAILURE": [
                r"grind(y|ing)?", r"tedious", r"chore", r"repetitive tasks?", r"boring farming", r"too much grind",
                r"inventory management", r"micro management", r"scarce resources?", r"hunger meter"
            ]
        },
        "Exploration": {
            "SUCCESS": [
                r"open world", r"fun explor(ation|ing)", r"beauti(ful|fy) world", r"map design", r"secrets? to find",
                r"biomes?", r"landmarks?", r"vast world", r"atmosphere"
            ],
            "FAILURE": [
                r"empty (world|map)", r"walking sim(ulator)?", r"nothing to do", r"boring map", r"barren",
                r"lifeless", r"too big", r"generic map", r"confusing map"
            ]
        },
        "Progression": {
            "SUCCESS": [
                r"progression system", r"rewarding", r"addictive loop", r"tech tree", r"good upgrades?",
                r"sense of progress(ion)?", r"unlock(s|ing)?", r"leveling up"
            ],
            "FAILURE": [
                r"slow progression", r"confusing", r"lack of (content|progression)", r"pointless", r"waste of time",
                r"hit a wall", r"endgame", r"early access", r"no content"
            ]
        }
    },

    # 5. Visual Novel (비주얼 노벨)
    "Visual Novel": {
        "Character": {
            "SUCCESS": [
                r"charming characters?", r"character develop(ment)?", r"great voice acting", r"cute characters?",
                r"deep characters?", r"lovable cast", r"relatable", r"personality", r"voice actors?", r"waifu"
            ],
            "FAILURE": [
                r"annoying characters?", r"flat characters?", r"cliche(d)?", r"bland personality", r"hated the mc",
                r"shallow", r"stereotyp(e|ical)", r"bad acting", r"cringey"
            ]
        },
        "Story": {
            "SUCCESS": [
                r"engaging story", r"emotional", r"masterpiece", r"well written", r"immersive plot", r"great writing",
                r"plot twist", r"tear jerker", r"compelling", r"lore"
            ],
            "FAILURE": [
                r"boring story", r"predictable", r"bad(ly)? writ(ing|ten)", r"bad translat(ion|ed)", r"plot holes?",
                r"pacing issues?", r"slow start", r"typos?", r"grammar", r"confusing plot"
            ]
        },
        "Choice": {
            "SUCCESS": [
                r"choices? matter", r"multiple endings?", r"branching paths?", r"replay value", r"consequences?",
                r"impactful choices?", r"routes?"
            ],
            "FAILURE": [
                r"illusion of choice", r"linear story", r"kinetic novel", r"one ending", r"choices? (dont|don't) matter",
                r"railroad(ed|ing)?", r"forced"
            ]
        }
    },

    # 6. Sports (스포츠)
    "Sports": {
        "Physics": {
            "SUCCESS": [
                r"realis(tic|m)", r"physics engine", r"immersi(on|ve)", r"authenti(c|city)", r"good animations?",
                r"ball physics?", r"weight", r"momentum"
            ],
            "FAILURE": [
                r"arcade(y)?", r"scripted events?", r"unrealis(tic|m)", r"clunky animat(ions?)", r"glitch(y|es)?",
                r"broken physics?", r"bugs?", r"collision", r"sliding"
            ]
        },
        "AI": {
            "SUCCESS": [
                r"smart ai", r"intelligent ai", r"challenging ai", r"good cpu", r"adaptive ai", r"realistic ai"
            ],
            "FAILURE": [
                r"stupid ai", r"dumb ai", r"broken ai", r"scripting", r"cheating ai", r"braindead",
                r"rubber band(ing)?", r"easy ai", r"unfair ai"
            ]
        },
        "Game Flow": {
            "SUCCESS": [
                r"smooth gameplay", r"fair match(es)?", r"good pace", r"balanced rules?", r"fun mode", r"career mode"
            ],
            "FAILURE": [
                r"momentum", r"handicap", r"pay to win", r"p2w", r"casino", r"loot box(es)?", r"microtransactions?",
                r"scripted", r"predatory", r"cash grab", r"yearly release"
            ]
        }
    },

    # 7. Roguelike (로그라이크)
    "Roguelike": {
        "RNG": {
            "SUCCESS": [
                r"good variety", r"procedural(ly)? generat(ed|ion)", r"fresh runs?", r"fair randomness",
                r"unique runs?", r"good rng"
            ],
            "FAILURE": [
                r"rng heavy", r"bad luck", r"unfair rng", r"too random", r"bad seed", r"rng dependent",
                r"unlucky", r"bullshit"
            ]
        },
        "Replayability": {
            "SUCCESS": [
                r"replay value", r"high replayability", r"addict(ive|ing)", r"thousands? of hours?",
                r"infinite content", r"one more run", r"hooked", r"tons of unlock(s|ables)?"
            ],
            "FAILURE": [
                r"repetitive", r"boring", r"samey", r"lack of content", r"grind(y)?", r"shallow", r"short"
            ]
        },
        "Synergy": {
            "SUCCESS": [
                r"good synerg(y|ies)", r"build variety", r"good comb(os?|inations?)", r"powerful builds?",
                r"strategic", r"synergiz(e|es|ing)?"
            ],
            "FAILURE": [
                r"weak builds?", r"unbalan(ced|ce)", r"useless items?", r"lack of synergy", r"meta slave",
                r"nerf(ed)?", r"broken items?"
            ]
        }
    },

    # 8. Card & Board (카드/보드)
    "Card & Board": {
        "Strategy": {
            "SUCCESS": [
                r"strategic depth", r"tactic(al|s)?", r"skill based", r"balanced? (meta|deck)", r"mind games?",
                r"complex(ity)?", r"thinking", r"outplay"
            ],
            "FAILURE": [
                r"unbalan(ced|ce)", r"broken (meta|cards?)", r"braindead", r"no skill", r"op cards?",
                r"net deck", r"stale meta", r"power creep"
            ]
        },
        "Accessibility": {
            "SUCCESS": [
                r"easy to learn", r"good tutorial", r"intuitiv(e|eness)", r"accessib(le|ility)", r"beginner friendly",
                r"simple to play", r"clean ui"
            ],
            "FAILURE": [
                r"steep learning curve", r"complex", r"confusing", r"hard to learn", r"overwhelming",
                r"cluttered ui", r"bad tutorial", r"not new player friendly"
            ]
        },
        "Luck": {
            "SUCCESS": [
                r"fair rng", r"fun randomness", r"f2p friendly", r"generous", r"fair economy"
            ],
            "FAILURE": [
                r"rng fest", r"pay to win", r"p2w", r"expensive", r"paywall", r"greedy devs?",
                r"cash grab", r"money hungry", r"luck based", r"coin flip"
            ]
        }
    }
    
}


GENRE_FACTORS.update(NEW_GENRE_FACTORS)

def analyze_sentiment_api(client, text):
    try:
        if not text or pd.isna(text):
            return 0.0, 0.0

        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT, language='en')
        response = client.analyze_sentiment(document=document)
        
        score = response.document_sentiment.score
        magnitude = response.document_sentiment.magnitude
        
        return score, magnitude
    
    except Exception as e:
        return 0.0, 0.0

def analyze_keywords_vectorized(df_reviews, df_game_list, genre_factors_dict):

    df_results = df_reviews[['appid', 'review']].copy()
    
    appid_to_genre = df_game_list.set_index('appid')['Selected_Genre'].to_dict()
    appid_to_group = df_game_list.set_index('appid')['Group'].to_dict()
    
    df_results['genre'] = df_results['appid'].map(appid_to_genre)
    df_results['group'] = df_results['appid'].map(appid_to_group)
    
    all_keyword_cols = []
    
    df_list = []
    
    for genre, factors in genre_factors_dict.items():
        
        df_genre = df_results[df_results['genre'] == genre].copy()
        
        if df_genre.empty:
            continue
            
        genre_keyword_cols = []

        for category, factor_dict in factors.items():
            
            success_patterns = '|'.join(factor_dict.get('SUCCESS', []))
            success_col_name = f"{genre}_SUCCESS_{category}"
            if success_patterns:
                df_genre[success_col_name] = df_genre['review'].str.lower().str.count(success_patterns, flags=re.IGNORECASE).fillna(0)
                genre_keyword_cols.append(success_col_name)

            failure_patterns = '|'.join(factor_dict.get('FAILURE', []))
            failure_col_name = f"{genre}_FAILURE_{category}"
            if failure_patterns:
                df_genre[failure_col_name] = df_genre['review'].str.lower().str.count(failure_patterns, flags=re.IGNORECASE).fillna(0)
                genre_keyword_cols.append(failure_col_name)

        top_mask = df_genre['group'] == 'Top'
        bottom_mask = df_genre['group'] == 'Bottom'
        
        for col in genre_keyword_cols:
            if '_FAILURE_' in col:
                df_genre.loc[top_mask, col] = 0
            elif '_SUCCESS_' in col:
                df_genre.loc[bottom_mask, col] = 0
                
        df_list.append(df_genre)
        all_keyword_cols.extend(genre_keyword_cols)

    if not df_list:
        return pd.DataFrame()
        
    df_combined = pd.concat(df_list, ignore_index=True)
    
    df_keyword_counts = df_combined.groupby('appid', dropna=False)[list(set(all_keyword_cols))].sum().reset_index()
    
    return df_keyword_counts

def calculate_keyword_ratios(df_game_list, df_keyword_counts):
    
    df_results = pd.merge(df_game_list[['appid', 'Review_Count']], df_keyword_counts, on='appid', how='left')
    df_results = df_results.fillna(0)
    
    keyword_cols = [col for col in df_results.columns if col not in ['appid', 'Review_Count']]
    
    for col in keyword_cols:
        ratio_col = f'{col}_Ratio'
        df_results[ratio_col] = df_results.apply(
            lambda row: row[col] / row['Review_Count'] if row['Review_Count'] > 0 else 0.0, axis=1
        )
        
    ratio_cols = [col for col in df_results.columns if col.endswith('_Ratio')]
    
    df_final = df_results[['appid'] + ratio_cols]
    
    return df_final

def calculate_sentiment_averages(df_game_list, df_reviews_sentiment):
    
    sentiment_averages = df_reviews_sentiment.groupby('appid')[['sentiment_score', 'sentiment_magnitude']].mean().reset_index()
    
    df_final = pd.merge(df_game_list, sentiment_averages, on='appid', how='left')
    
    df_final[['sentiment_score', 'sentiment_magnitude']] = df_final[['sentiment_score', 'sentiment_magnitude']].fillna(0.0)
    
    return df_final


if __name__ == '__main__':
    BASE_PATH = "C:\\Users\\minjh\\Downloads\\dataproject5team-feature-kimguenseok-redit\\dataproject5team-feature-kimguenseok-redit\\review_analyze_code_and_result\\"
    
    REVIEWS_FILE_PATH = BASE_PATH + "steam_reviews_top50_each_game.csv" 
    
    TOP_GAMES_PATH = BASE_PATH + "final_top_20_per_genre_fixed.csv"
    BOTTOM_GAMES_PATH = BASE_PATH + "final_bottom_20_per_genre_fixed.csv"
    
    OUTPUT_FILE_PATH = BASE_PATH + "final_analysis_results_3_categories.csv"
    GENRE_AVERAGES_PATH = BASE_PATH + "genre_category_averages.csv"

    try:
        df_reviews = pd.read_csv(REVIEWS_FILE_PATH)
    except FileNotFoundError:
        print(f"오류: 리뷰 파일 '{REVIEWS_FILE_PATH}'을(를) 찾을 수 없습니다.")
        print("경로를 확인하거나, 'steam_reviews_top50_each_game.csv' 파일을 해당 경로에 놓아주세요.")
        exit()

    try:
        df_top_games = pd.read_csv(TOP_GAMES_PATH)
        df_bottom_games = pd.read_csv(BOTTOM_GAMES_PATH)
    except FileNotFoundError as e:
        print(f"오류: 상위/하위 게임 목록 파일 중 하나를 찾을 수 없습니다: {e.filename}")
        print("해당 파일을 BASE_PATH에 놓아주세요.")
        exit()

    df_top_games['Group'] = 'Top'
    df_bottom_games['Group'] = 'Bottom'
    
    df_game_list = pd.concat([df_top_games, df_bottom_games], ignore_index=True).drop_duplicates(subset=['appid'])
    
    target_genres = list(GENRE_FACTORS.keys())
    df_game_list = df_game_list[df_game_list['Selected_Genre'].isin(target_genres)].copy()
    
    target_appids = df_game_list['appid'].unique()
    df_reviews_filtered = df_reviews[df_reviews['appid'].isin(target_appids)].copy()
    
    actual_review_counts = df_reviews_filtered.groupby('appid').size().reset_index(name='Review_Count')
    df_game_list = df_game_list.drop(columns=['Review_Count'], errors='ignore')
    df_game_list = pd.merge(df_game_list, actual_review_counts, on='appid', how='left')
    df_game_list['Review_Count'] = df_game_list['Review_Count'].fillna(0).astype(int)

    total_reviews_count = len(df_reviews_filtered)
    print(f"--- 8개 장르 전체 분석을 시작합니다. ---")
    print(f"분석 대상 게임 수: {len(df_game_list)}개. 총 리뷰 수: {total_reviews_count}개")

    df_reviews_sentiment = pd.DataFrame({
        'appid': df_reviews_filtered['appid'],
        'sentiment_score': [0.0] * len(df_reviews_filtered),
        'sentiment_magnitude': [0.0] * len(df_reviews_filtered),
    })

    print("키워드 분석 (3개 카테고리, 벡터화)을 시작합니다...")
    df_keyword_counts = analyze_keywords_vectorized(df_reviews_filtered, df_game_list, GENRE_FACTORS)
    print("키워드 분석 완료.")
    
    df_final_sentiment = calculate_sentiment_averages(df_game_list, df_reviews_sentiment)
    
    
    df_final_keywords_ratios = calculate_keyword_ratios(df_game_list, df_keyword_counts)
    
    df_final = pd.merge(df_final_sentiment, df_final_keywords_ratios, on='appid', how='left')

    df_final.to_csv(OUTPUT_FILE_PATH, index=False, encoding='utf-8-sig')
    print(f"\n게임별 분석 결과가 다음 파일에 저장되었습니다: {OUTPUT_FILE_PATH}")
