# ============================================================
# module : rd-plot
# author : peter swinburne
# date   : 05/21/2021
# brief  : plot reading utility
# ============================================================
from tkinter import filedialog
import tkinter as tk
from tkinter import *
from tkinter import ttk
#from tkinter import font
from PIL import Image
import numpy as np
import pandas as pd
import os

debug = False


# ============================================================
def using_np():
    global filename, progress_output_text
    global min_value, max_value, min_depth_val, max_depth_val
    global head_tail, im, width, depth
    global data, red, green, blue, alpha

    gthres = 20
    bthres = 150
    dthres = 40
    bgr = 0
    bgg = 0
    bgb = 0
    green_areas  = (red > (green - gthres)) & (blue > (green - gthres))
    grey_areas   = (red == green) & (red == blue) & (blue == green) # works
    bright_areas = (red > bthres) & (green > bthres) & (blue > bthres) # works
    dark_areas   = (red < dthres) & (green < dthres) & (blue < dthres)

    data[..., :-1][bright_areas.T] = (bgr, bgg, bgb) # Transpose back needed
    data[..., :-1][grey_areas.T]   = (bgr, bgg, bgb) # Transpose back needed
    data[..., :-1][dark_areas.T]   = (bgr, bgg, bgb) # Transpose back needed
    data[..., :-1][green_areas.T]  = (bgr, bgg, bgb) # Transpose back needed

    im2 = Image.fromarray(data)
    if debug:
        im2.show()
    rgb_im = im2.convert('RGB')
    rgb_im.save('processed.jpg')

    # calculate xvals from image
    edge_offset = 8
    vals = np.zeros((depth, 2))
    for y in range(0, depth):
        vals[y, 0] = y
        for x in range(edge_offset, width - edge_offset):
            pix = im2.getpixel((x,y))
            if (pix[0] != bgr) & (pix[0] > dthres):
                val_s = x
                val_e = 0
                for x2 in range(x+1, width):
                    pix = im2.getpixel((x2, y))
                    if pix[0] != bgr:
                        continue
                    else:
                        val_e = x2 - 1
                        break
                x_val = val_s + (int((val_e - val_s) / 2))
                vals[y,1] = x_val
                break

    # delete first 4 rows
    vals = np.delete(vals, 0, 0)
    vals = np.delete(vals, 0, 0)
    vals = np.delete(vals, 0, 0)
    depth = depth - 3

    # detect holes in the data
    for y in range(0, depth):
        if vals[y,1] == 0.0:
            if  y != depth - 1:
                if (vals[y+1,1] != 0.0):
                    # average the mid point
                    vals[y,1] = (vals[y-1,1] + vals[y+1,1]) / 2.0
                else:
                    # use the last point
                    vals[y, 1] = vals[y - 1, 1]
            else:
                vals[y, 1] = vals[y - 1, 1]

    # scale the height and the x values
    min_depth_int = int(min_depth_val.get())
    max_depth_int = int(max_depth_val.get())
    min_value_int = int(min_value.get())
    max_value_int = int(max_value.get())
    num_rows, num_cols = vals.shape
    ydelta = (max_depth_int - min_depth_int) / (num_rows - 1)
    xdelta = (max_value_int - min_value_int) / width
    vals[0,0] = min_depth_int
    vals[0,1] = vals[0,1] * xdelta
    for y in range(1, depth):
        vals[y, 0] = vals[y - 1, 0] + ydelta
        vals[y, 1] = vals[y, 1] * xdelta        #x scaling is not correct !!!

    df = pd.DataFrame(vals)

    # construct output path and file name
    # @@@ output filename is wrong... it contains jpg and should not
    new_filename = head_tail[1].split()[0] + ".csv"
    output_path_file = os.path.join(head_tail[0], new_filename)
    df.to_csv(output_path_file, header=["D", "V"], float_format="%.3f", index=False)
    progress_output_text.set("Complete")


# =============================================
def tk_start():
    global filename, root, progress_output_text
    global min_value, max_value, min_depth_val, max_depth_val
    global head_tail, im, width, depth
    global data, red, green, blue, alpha

    content = ttk.Frame(root)
    content.grid(column=0, row=0)

    root.title("Color Curve Digitizer")
    root.maxsize(600, 600)

    style_path = ttk.Style()
    style_path.configure("style_path.TLabel", background='lightgreen')
    path_label = ttk.Label(content, text="      ")
    path_label['style'] = "style_path.TLabel"
    path_label.grid(row=0, column=0, columnspan=3)

    style_file = ttk.Style()
    style_file.configure("style_file.TLabel", background='green', foreground='white')
    file_label = ttk.Label(content, text="      ")
    file_label['style'] = "style_file.TLabel"
    file_label.grid(row=1, column=0, columnspan=3)

    min_value = StringVar(value="0")
    min_entry = ttk.Entry(content, textvariable=min_value, justify='center')
    min_entry.grid(row=2, column=0)

    min_label = ttk.Label(content, text="Min Value")
    min_label.grid(row=2, column=1)

    max_value = StringVar(value="100")
    max_entry = ttk.Entry(content, textvariable=max_value, justify='center')
    max_entry.grid(row=3, column=0)

    max_label = ttk.Label(content, text="Max Value")        # , fg="green"
    max_label.grid(row=3, column=1)

    min_depth_val = StringVar(value="1000")
    min_depth = ttk.Entry(content, textvariable=min_depth_val, justify='center')
    min_depth.grid(row=4, column=0)

    min_depth_label = ttk.Label(content, text="Min Height")        # , fg="green"
    min_depth_label.grid(row=4, column=1)

    max_depth_val = StringVar(value="2000")
    max_depth = ttk.Entry(content, textvariable=max_depth_val, justify='center')
    max_depth.grid(row=5, column=0)

    max_depth_label = ttk.Label(content, text="Max Height")        # , fg="green"
    max_depth_label.grid(row=5, column=1)

    # @@@ linear should be selected but for some reason it is not...
    var = IntVar()
    var.set(1)
    x_axis_label = ttk.Label(content, text="X-Axis type")
    rb1 = ttk.Radiobutton(content, text="Linear", variable=var, value=0)
    rb2 = ttk.Radiobutton(content, text="Log", variable=var, value=1)
    rb1.grid(row=6, column=0)
    rb2.grid(row=6, column=1)
    x_axis_label.grid(row=6, column=2)

    progress_output_text = StringVar(value='Ready')
    progress_output = ttk.Entry(content, textvariable=progress_output_text, justify='center')
    progress_output.grid(row=7, column=0, columnspan=2)
    progress_output["state"] = tk.DISABLED

    execute_button = ttk.Button(content, text="Execute", command=using_np)       # fg="blue",
    execute_button.grid(row=8, column=0)

    quit_button = ttk.Button(content, text="Quit", command=root.destroy)     # fg="red",
    quit_button.grid(row=8, column=1)

    head_tail = os.path.split(filename)
    path_label["text"] = head_tail[0]
    file_label["text"] = head_tail[1]

    # open the file
    im = Image.open(filename)
    im = im.convert('RGBA')
    width, depth = im.size

    # convert the file
    data = np.array(im)  # "data" is a height x width x 4 numpy array
    red, green, blue, alpha = data.T  # Temporarily unpack the bands for readability
    print("data shape : ", data.shape)

    # find colors in file
    # choose a height, say 25 % of the height
    pdepth = int((depth * 25) / 100)
    color_choose = data[pdepth,:,:]
    print("color shape : ", color_choose.shape)
    colorbar = color_choose
    for i in range(0, 20):
        colorbar = np.append(colorbar, color_choose)

    colorbar = np.append(colorbar, color_choose).reshape((22,width,4))
    print("colorbar shape     : ", colorbar.shape)

    im = Image.fromarray(colorbar)
    im.save("colorbar.png")
    # @@@ the "track in question always has a min and a max on the page
    # @@@ the application should allow the user to select the lefthand and righthand boundaries of the track

    # @@@ the user should be able to select the color of the track


# ============================================================
if __name__ == '__main__':
    # get the filename
    root = tk.Tk()
    root.withdraw()
    filename = filedialog.askopenfilename()
    root.destroy()

    # launch the app
    root = Tk()
    tk_start()

    root.mainloop()
