# ============================================================
# module     : rd-plot
# author     : peter.swinburne@fortaleza-consulting.com
# date       : 05/21/2021
# brief      : log plot reading utility
# updates by : 
# ============================================================

##TO DO -> support for log, support for black color curves

import cv2
import numpy as np
from tkinter import ttk
from tkinter import filedialog
from tkinter import *
import tkinter as tk 
from tkinter import Tk
from numpy.core.defchararray import upper
import ctypes
from numpy import asarray
import PIL
from PIL import Image
import pandas as pd

user_depth = 0
user_color = 0
user_xmin = 0
user_xmax = 0
user_ymin = 0
user_ymax = 0
edges = np.zeros((2,2),np.int)
counter = 0


def get_edges():
    global col1, col2, image

    Tk().withdraw() 
    filename = filedialog.askopenfilename()
    im = cv2.imread(filename)

    #resize to fit window
    image = cv2.resize(im, (1000,800))

    #dialog with instructions
    ctypes.windll.user32.MessageBoxW(0, "Please select your desired track's left and right boundaries", "Color Curve Digitizer", 1)

    while True:

        for x in range (0,2):
                cv2.circle(image, (edges[x][0],edges[x][1]),2,(0,0,0),cv2.FILLED)

        if counter == 2:
        #collect first and last columns
            col1 = (edges[0][0])
            col2 = (edges[1][0])

            cv2.destroyAllWindows()

            break #continue once two edges are detected

        cv2.imshow("Image", image)
        cv2.setMouseCallback("Image", findEdges)
        cv2.waitKey(1)


def user_input_win():
    global user_color, user_xmin, user_xmax, user_ymin, user_ymax
    global col1, col2, color_entry, r, color
    global xmax_entry, xmin_entry, ymax_entry, ymin_entry

    root = tk.Tk()
    root.title("Color Curve Digitizer")

    #center window
    w = 250
    h = 300
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w,h,x,y))

    depth = tk.StringVar()
    xmin = tk.StringVar()
    xmax = tk.StringVar()
    ymin = tk.StringVar()
    ymax = tk.StringVar()

    #input frame
    entry = ttk.Frame(root)
    entry.pack(padx=2, pady=0, fill='x', expand=True)

    xmin_label = ttk.Label(entry, text = "X Min").pack()
    xmin_entry = ttk.Entry(entry, textvariable = xmin, justify = 'center')
    xmin_entry.pack()
        
    xmax_label = ttk.Label(entry, text = "X Max").pack()
    xmax_entry = ttk.Entry(entry, textvariable = xmax, justify='center')
    xmax_entry.pack()

    ymin_label = ttk.Label(entry, text = "Y Min").pack()
    ymin_entry = ttk.Entry(entry, textvariable = ymin, justify = 'center')
    ymin_entry.pack()
        
    ymax_label = ttk.Label(entry, text = "Y Max").pack()
    ymax_entry = ttk.Entry(entry, textvariable = ymax, justify='center')
    ymax_entry.pack()

    colors = [('Green', 'G'),('Red', 'R'),('Blue', 'B'),('Black', 'BL')]
    color_entry = tk.StringVar(entry) #pass name of frame containing radiobuttons to update button variable
    color_entry.set(" ")

    colors_label = ttk.Label(entry, text = "Track Color").pack()
    for text, color in colors:
        ttk.Radiobutton(entry, text=text, variable=color_entry, value=color).pack(fill='y', expand=True)

    #button
    digitize_button = ttk.Button(root, text="Digitize", command=masking)
    digitize_button.pack(side='bottom')

    root.mainloop()


def findEdges(event,x,y, flags, params):
    global counter, user_depth, user_color, col1, col2
    global depth_entry, color_entry, track_slice

    if event == cv2.EVENT_LBUTTONDOWN:
        edges[counter] = x,y
        counter = counter + 1


def masking():
    global user_color, edges, col1, col2, color_entry, newfile
    global user_xmin, user_xmax, user_ymin, user_ymax, rescaled_slice
    #create img from track selection
    np.set_printoptions(threshold=np.inf)
    user_color = color_entry.get()

    new_image = image[0:int(8000),int(col1):int(col2)]

    #convert selection to HSV for masking
    hsv = cv2.cvtColor(new_image, cv2.COLOR_BGR2HSV)

    #set color boundaries
    upper_green = np.array([180,255,235])
    lower_green = np.array([12,35,15])
    upper_blue = np.array([185, 185, 244])
    lower_blue = np.array([60, 50, 255])
    upper_red = np.array([10, 255, 255])
    lower_red = np.array([0, 100, 50])

    #create masks
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    red_mask = cv2.inRange(hsv, lower_red, upper_red)
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue) 
        
    #create masked images based on user color selection
    if user_color=='G':
        track_slice = cv2.bitwise_and(new_image, new_image, mask=green_mask)
        
    elif user_color=='R':
        track_slice = cv2.bitwise_and(new_image, new_image, mask=red_mask)
        
    elif user_color=='B':
        track_slice = cv2.bitwise_and(new_image, new_image, mask=blue_mask)

    trackimg = cv2.imwrite("selection.png", track_slice, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    ## 1. calculate position of color pixels
    im = Image.open('selection.png')
    im2arr = np.array(im)
    width, depth = im.size
    edge_offset = 8
    vals = np.zeros((depth,2))
    for y in range(0,depth):
        vals[y,0] = y
        for x in range(edge_offset, width - edge_offset):
            pix = im.getpixel((x,y))
            if (pix[0] != 0):
                val_s = x
                val_e = 0
                for x2 in range(x+1, width):
                    pix = im.getpixel((x2, y))
                    if pix[0] != 0:
                        continue
                    else:
                        val_e = x2 - 1
                        break
                x_val = val_s + (int((val_e - val_s) / 2))
                vals[y,1] = x_val
                break

    #detect holes in data
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

    df = pd.DataFrame(vals)

    #find min,max of df
    min_x = df[0].min()
    max_x = df[0].max()

    min_y = df[1].min()
    max_y = df[1].max()

    ## get user min, max
    user_xmax = int(xmax_entry.get())
    user_xmin = int(xmin_entry.get())

    user_ymax = int(ymax_entry.get())
    user_ymin = int(ymin_entry.get())

    ## column range max - min, user range user max - user min
    range_x = max_x - min_x
    range_y = max_y - min_y

    user_rangex = user_xmax - user_xmin
    user_rangey = user_ymax - user_ymin

    ## expansion rate is user range/column range
    exprate_x = (user_rangex / range_x)
    exprate_y = (user_rangey / range_y)

    ## scale
    df[0] = df[0].apply(lambda x: (x - min_x)*exprate_x + user_xmin)
    df[1] = df[1].apply(lambda x: (x - min_y)*exprate_y + user_ymin)

    ## 10. save new array as csv
    df.to_csv("processed.csv", header=["D", "V"], float_format="%.3f", index=False)

    quit_window()


def quit_window():
    root = tk.Tk()
    root.title("Color Curve Digitizer")

    #center window
    newfile = "'processed.csv'"
    w = 400
    h = 50
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w,h,x,y))
    
    depth_label = ttk.Label(root, text = "Your selection has been processed and saved as {}.".format(newfile), anchor=tk.CENTER)
    depth_label.pack(padx=5, pady=5, fill='x', expand=True)

    Button(root, text="Done", command=quit).pack()

    root.mainloop()
    

if __name__ == '__main__':

    get_edges()
    user_input_win()