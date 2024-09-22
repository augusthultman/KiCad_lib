import sys
import tkinter as tk
from tkinter import ttk
from tkinter import *


root = Tk()

# This is the section of code which creates the main window
root.geometry('600x560')
#root.configure(background='#F0F8FF')
root.title('Resistor Creator')

# Create resistor name
def generateText(userInputs):
	return "RES_"+userInputs["size"]+"_"+userInputs["value"]+"_"+userInputs["resType"]+"_"+userInputs["tol"]+"_"+userInputs["pwr"]

# Function to get the user inputs from the text input boxes
def getAllInputs():
	userInputs = dict(
		value = tInput_value.get(),
		size = combo_size.get(),
		pwr = tInput_pwr.get(),
		tol = tInput_tol.get(),
		resType = tInput_type.get(),
		mfgOne = tInput_mfgOne.get(),
		mfgTwo = tInput_mfgTwo.get(),
		mfgThree = tInput_mfgThree.get(),
		mfgOnePN = tInput_mfgOnePN.get(),
		mfgTwoPN = tInput_mfgTwoPN.get(),
		mfgThreePN = tInput_mfgThreePN.get(),
		datasheetOne = tInput_datasheetOne.get(),
		datasheetTwo = tInput_datasheetTwo.get(),
		datasheetThree = tInput_datasheetThree.get())
	return userInputs

mfgOne = tk.StringVar()
mfgTwo = tk.StringVar()
mfgThree = tk.StringVar()
pnOne = tk.StringVar()
pnTwo = tk.StringVar()
pnThree = tk.StringVar()
DSOne = tk.StringVar()
DSTwo = tk.StringVar()
DSThree = tk.StringVar()
previewText = tk.StringVar()

# this is the function called when the button is clicked
def btnClickFunction_preview():
	print('clicked Preview')
	text = generateText(getAllInputs())
	print("Resistor name: ")
	print(text)
	previewText.set(text)#preview.insert(0, text)

# this is the function called when the button is clicked
def btnClickFunction_gen():
	print('clicked Generate')

def btnClickFunction_yageo():
	DSOne.set("https://www.yageo.com/upload/media/product/app/datasheet/rchip/pyu-rc_group_51_rohs_l.pdf")
	mfgOne.set("Yageo")
	pnOne.set("RC")

def btnClickFunction_stackpole():
	DSTwo.set("https://www.seielect.com/catalog/sei-rmcf_rmcp.pdf")
	mfgTwo.set("Stackpole Electronics Inc")
	pnTwo.set("RMCF")

def btnClickFunction_koa():
	DSThree.set("https://www.koaspeer.com/pdfs/RK73H.pdf")
	mfgThree.set("KOA Speer")
	pnThree.set("RK73H1ETTD")

# Create a combo box
combo_size= ttk.Combobox(root, values=['0402', '0603', '0805', '1206'], font=('arial', 12, 'normal'), width=10)
combo_size.place(x=38, y=78)
combo_size.current(1)

# Create textboxes!
Label(root, text = "Value: (1R2, 10K1..)").place(x=38, y=15)
tInput_value=Entry(root)
tInput_value.place(x=38, y=38)

Label(root, text = "Tolerance: (0.1%, 1%..)").place(x=198, y=15)
tInput_tol=Entry(root)
tInput_tol.place(x=198, y=38)

Label(root, text = "Type: (TKF, TNF..)").place(x=358, y=15)
tInput_type=Entry(root)
tInput_type.place(x=358, y=38)

Label(root, text = "Mfg:").place(x=2, y=118)
tInput_mfgOne=Entry(root, textvariable=mfgOne)
tInput_mfgOne.place(x=38, y=118)

Label(root, text = "Mfg:").place(x=2, y=188)
tInput_mfgTwo=Entry(root, textvariable=mfgTwo)
tInput_mfgTwo.place(x=38, y=188)

Label(root, text = "Mfg:").place(x=2, y=258)
tInput_mfgThree=Entry(root, textvariable=mfgThree)
tInput_mfgThree.place(x=38, y=258)

Label(root, text = "P/N:").place(x=2, y=148)
tInput_mfgOnePN=Entry(root, textvariable=pnOne)
tInput_mfgOnePN.place(x=38, y=148)

Label(root, text = "P/N:").place(x=2, y=218)
tInput_mfgTwoPN=Entry(root, textvariable=pnTwo)
tInput_mfgTwoPN.place(x=38, y=218)

Label(root, text = "P/N:").place(x=2, y=288)
tInput_mfgThreePN=Entry(root, textvariable=pnThree)
tInput_mfgThreePN.place(x=38, y=288)

Label(root, text = "Pwr:").place(x=2, y=338)
Label(root, text = "1/10W, 1/16W..").place(x=180, y=338)
tInput_pwr=Entry(root)
tInput_pwr.place(x=38, y=338)

Label(root, text = "Datasheet:").place(x=198, y=125)
tInput_datasheetOne=Entry(root, textvariable=DSOne)
tInput_datasheetOne.place(x=198, y=148)
Button(root, text='Use Yageo RC', bg='#F0F8FF', font=('arial', 7, 'normal'), command=btnClickFunction_yageo).place(x=350, y=148)

Label(root, text = "Datasheet:").place(x=198, y=195)
tInput_datasheetTwo=Entry(root, textvariable=DSTwo)
tInput_datasheetTwo.place(x=198, y=218)
Button(root, text='Use Stackpole RMCF', bg='#F0F8FF', font=('arial', 7, 'normal'), command=btnClickFunction_stackpole).place(x=350, y=218)

Label(root, text = "Datasheet:").place(x=198, y=265)
tInput_datasheetThree=Entry(root, textvariable=DSThree)
tInput_datasheetThree.place(x=198, y=288)
Button(root, text='Use Koa RK73H', bg='#F0F8FF', font=('arial', 7, 'normal'), command=btnClickFunction_koa).place(x=350, y=288)

preview = Entry(root, width = 60, textvariable=previewText)
preview.place(x=38, y=450)
preview.insert(0, "Preview..")

# Create buttons!
Button(root, text='Preview', bg='#F0F8FF', font=('arial', 12, 'normal'), command=btnClickFunction_preview).place(x=38, y=380)
Button(root, text='Generate', bg='#F0F8FF', font=('arial', 12, 'normal'), command=btnClickFunction_gen).place(x=158, y=380)

root.mainloop()
