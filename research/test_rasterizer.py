try:
    import custom_rasterizer
    print("custom_rasterizer imported successfully")
    print(dir(custom_rasterizer))
except ImportError:
    print("custom_rasterizer not found")
except Exception as e:
    print(f"Error importing custom_rasterizer: {e}")
