#!/usr/bin/env python3
"""
Common utilities for FORMLÆRE analysis.
Defines Töpfer-style, material colors, and data loading.
"""
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
MESH_PATH = ROOT / 'analysis' / 'mesh_features.csv'
CAT_PATH = ROOT / 'STOLAR' / 'STOLAR.csv'
FIG_OUT = ROOT / 'analysis' / 'figures'
FIG_OUT.mkdir(exist_ok=True)

# Palette — Töpfer-Technical with Functional Color
INK = '#1a1a1a'
PAPER = '#fbfbf8'
GRID = '#e8e7df'
CORE_AREA = '#FFF9E6'

MAT_COLORS = {
    'tre':     '#A88C7B',
    'metall':  '#5C6B7F',
    'plast':   '#C8a268',
    'tekstil': '#4F7B52',
    'anna':    '#bbbbbb'
}

def apply_style():
    style = {
        'figure.facecolor': 'white',
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'axes.facecolor': PAPER,
        'axes.edgecolor': INK,
        'axes.labelcolor': INK,
        'axes.titlecolor': INK,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.linewidth': 0.6,
        'xtick.color': INK,
        'ytick.color': INK,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'font.family': 'serif',
        'font.serif': ['EB Garamond', 'Garamond', 'Palatino', 'Libertine', 'serif'],
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 9,
        'legend.frameon': False,
        'legend.fontsize': 8,
        'lines.linewidth': 0.8,
        'patch.linewidth': 0.5,
    }
    plt.rcParams.update(style)

def load_stolar():
    mesh = pd.read_csv(MESH_PATH)
    cat = pd.read_csv(CAT_PATH, encoding='utf-8')
    rename = {cat.columns[i]: c for i, c in enumerate([
        'Namn','Bilete','Fra','Mat','MatK','Nasjmus','ID','PStad','Prod','Til',
        'GLB','Vekt','Nasj','URL','Emneord','Erverving','SH','Stil','Tekn',
        'Br','Dat','Dj','Ho','Nemn','Hundre',
    ])}
    cat = cat.rename(columns=rename)
    for c in ['Fra','Br','Ho','Dj']:
        cat[c] = pd.to_numeric(cat[c], errors='coerce')
    
    def matgrp(s):
        s = (s or '').lower()
        if 'plast' in s: return 'plast'
        if 'stål' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','furu','mahogni','teak','bjørk','bøk','asp']): return 'tre'
        if any(x in s for x in ['tekstil','lær','skinn','stoff','ull']): return 'tekstil'
        return 'anna'
    cat['matgr'] = cat.Mat.apply(matgrp)
    return mesh, cat
