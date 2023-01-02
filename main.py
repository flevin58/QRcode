from tkinter import Menu, filedialog as fd, messagebox as mb
from tkinter.colorchooser import askcolor
from customtkinter import CTk, CTkTextbox, CTkLabel, CTkButton, CTkFrame, CTkSlider
from PIL import ImageTk, Image, ImageGrab
import cv2
from qrcode import QRCode
from qrcode.constants import ERROR_CORRECT_L
from io import BytesIO
from config import *

class Application(CTk):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Instance variables
        self.current_file:str = ''
        self.current_image:Image = None
        self.fg_color = DEFAULT_FG_COLOR
        self.bg_color = DEFAULT_BG_COLOR
        self.qr_image_size = DEFAULT_IMAGE_SIZE

        # CTk configuration
        self._set_appearance_mode('System')
        self.title('QRCode Generator')
        self.minsize(640,480)
        self.resizable(width=False, height=False)
        self.rowconfigure(index=4, weight=1)

#region Menu Bar
        menu_bar = Menu(self)
        filemenu = Menu(menu_bar, tearoff=0)
        filemenu.add_command(label='Open', command=self.load_image)
        filemenu.add_command(label='Save', command=self.save_image)
        filemenu.add_separator()
        filemenu.add_command(label='Quit', command=self.quit)
        menu_bar.add_cascade(label='File', menu=filemenu)
        self.config(menu=menu_bar)
#endregion

#region Frames

        # QRcode Image at left
        img = Image.new('RGB',(DEFAULT_IMAGE_SIZE, DEFAULT_IMAGE_SIZE),(255,255,255))
        self.default_image = ImageTk.PhotoImage(img)

        self.image_label = CTkLabel(self, text='', image=self.default_image)
        self.image_label.grid(row=0, column=0, padx=20, rowspan=4)

        # Buttons in the middle

        empty1 = CTkLabel(self, text=' ')
        empty1.grid(row=0, column=1)

        generate_button = CTkButton(self, text='<< Convert', command=self.generate_code)
        generate_button.grid(row=1, column=1)

        read_button = CTkButton(self, text='Read >>', command=self.read_code)
        read_button.grid(row=2, column=1)

        empty2 = CTkLabel(self, text=' ')
        empty2.grid(row=3, column=1)

        # Text Box at right
        self.text_box = CTkTextbox(self, width=DEFAULT_IMAGE_SIZE, height=DEFAULT_IMAGE_SIZE)
        self.text_box.grid(row=0, column=2, padx=20, rowspan=4)

        # Configuration settings at the bottom
        conf_frame = CTkFrame(self)
        conf_frame.grid(row=4, column=0, columnspan=3)
        conf_frame.configure(border_color='red')

        slider_start_pos = 300
        self.image_size = CTkLabel(conf_frame, text=f'Image size: {slider_start_pos}', font=('Arial',20,'normal'))
        self.image_size.grid(row=0, column=0, padx=20)
        self.slider = CTkSlider(conf_frame, from_=200, to=2000, number_of_steps=36, command=self.slider_move)
        self.slider.set(slider_start_pos)
        self.slider.grid(row=0, column=1)

        self.fg_image = ImageTk.PhotoImage(Image.new(mode='RGB', size=(20,20), color=self.fg_color))
        qr_foreground = CTkLabel(conf_frame,
                                      text='Foreground: ',
                                      font=('Arial',20,'normal'),
                                      compound='right',
                                      image=self.fg_image)
        qr_foreground.grid(row = 1, column = 0)
        qr_foreground.bind('<Button-1>', self.fg_select)

        self.bg_image = ImageTk.PhotoImage(Image.new(mode='RGB', size=(20,20), color=self.bg_color))
        qr_background = CTkLabel(conf_frame,
                                      text='Background: ',
                                      font=('Arial',20,'normal'),
                                      compound='right',
                                      image=self.bg_image)
        qr_background.grid(row = 1, column = 1)
        qr_background.bind('<Button-1>', self.bg_select)

#endregion

    def fg_select(self, event):
        widget = event.widget
        self.fg_color, _ = askcolor(title='Choose QR Code foreground color')
        new_image = Image.new(mode='RGB', size=(20,20), color=self.fg_color)
        self.fg_image = ImageTk.PhotoImage(new_image)
        widget.configure(image=self.fg_image)

    def bg_select(self, event):
        widget = event.widget
        self.bg_color, _ = askcolor(title='Choose QR Code background color')
        new_image = Image.new(mode='RGB', size=(20,20), color=self.bg_color)
        self.bg_image = ImageTk.PhotoImage(new_image)
        widget.configure(image=self.bg_image)

    def slider_move(self, pos:float) -> None:
        """ Called when slider is moved. Updates label size value """
        self.qr_image_size = int(pos)
        self.image_size.configure(text = f'Image size: {self.qr_image_size}')

    def load_image(self) -> None:
        """ Called by 'Open' menu option, loads a QR Code image """
        filename = fd.askopenfilename(defaultextension='.png', title='Load QRCode')
        if filename != '':
            self.current_file = filename
            self.current_image = Image.open(filename).resize((300,300), RESAMPLING)
            self.image_label.configure(image=ImageTk.PhotoImage(self.current_image))

    def save_image(self) -> None:
        """ Called by 'Save' menu option, grabs image and saves it to disk """

        if not self.current_image:
            mb.showerror(title='Error', message='There is no QR Code image to convert to text!')
            return

        filename = fd.asksaveasfilename(defaultextension='.png', title='Save QRCode')
        if filename != '':
            size = (self.qr_image_size, self.qr_image_size)
            resized_image = self.current_image.resize(size, RESAMPLING)
            resized_image.save(filename)
           
    def generate_code(self) -> None:
        """ Called by '<<' button, generates QR Code from TextBox contents """

        # Get the TextBox contents, error in no text found
        data = self.text_box.get('0.0', 'end').strip()
        if data == '':
            mb.showerror(title='Error', message='There is no text to convert to QR Code!')
            return

        # Generate the QR Code image
        qr = QRCode(version=1,
                    error_correction=ERROR_CORRECT_L,
                    box_size=20,
                    border=2)
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color=self.fg_color, back_color=self.bg_color)

        # Set the image in the left pane label and memorize it in self.current_image
        mem_stream = BytesIO()
        image.save(stream=mem_stream)
        self.current_image = Image.open(mem_stream)
        self.current_image = self.current_image.resize((DEFAULT_IMAGE_SIZE,DEFAULT_IMAGE_SIZE), RESAMPLING)
        self.image_label.configure(image=ImageTk.PhotoImage(self.current_image))
 
    def read_code(self) -> None:
        """ Called by '>>' button, writes QR Code contents into TextBox """
        img = cv2.imread(self.current_file)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        self.text_box.delete('0.0', 'end')
        self.text_box.insert('0.0', data)

    def run(self) -> None:
        """ Called by main function to run the application """
        self.mainloop()

if __name__ == '__main__':
    app = Application()
    app.run()
