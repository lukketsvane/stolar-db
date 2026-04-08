import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# --- Style Configuration ---
BG_COLOR = '#ffffff'
TEXT_COLOR = '#000000'
LINE_COLOR = '#000000'
GRID_COLOR = '#eeeeee'
ACCENT_RAUD = '#000000' # Monochrome
ACCENT_GRAA = '#808080'

def setup_style():
    # Load fonts from analysis/scripts_viz/fonts
    base_path = os.path.dirname(__file__)
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    if os.path.exists(font_dir):
        for font_file in os.listdir(font_dir):
            if font_file.endswith('.ttf'):
                try:
                    fm.fontManager.addfont(os.path.join(font_dir, font_file))
                except:
                    pass

    plt.rcParams.update({
        'figure.facecolor': BG_COLOR,
        'axes.facecolor': BG_COLOR,
        'axes.edgecolor': TEXT_COLOR,
        'axes.linewidth': 0.6,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.labelcolor': TEXT_COLOR,
        'xtick.color': TEXT_COLOR,
        'ytick.color': TEXT_COLOR,
        'font.family': 'serif',
        'font.serif': ['EB Garamond'],
        'text.color': TEXT_COLOR,
        'patch.force_edgecolor': True,
        'patch.facecolor': 'none',
        'patch.edgecolor': TEXT_COLOR,
        'lines.linewidth': 0.8,
        'lines.solid_capstyle': 'butt',
        'legend.frameon': True,
        'legend.facecolor': 'white',
        'legend.edgecolor': 'black',
        'legend.fontsize': 9,
        'savefig.dpi': 300,
        'savefig.facecolor': BG_COLOR,
        'savefig.bbox': 'tight'
    })

def finalize_plot(ax, xlabel=None, ylabel=None, xlim=None, ylim=None):
    if xlabel: ax.set_xlabel(xlabel, fontname='EB Garamond', size=10)
    if ylabel: ax.set_ylabel(ylabel, fontname='EB Garamond', size=10)
    if xlim: ax.set_xlim(xlim)
    if ylim: ax.set_ylim(ylim)
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontname('EB Garamond')
        label.set_fontsize(9)
    plt.tight_layout()
