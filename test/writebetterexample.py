import base64
import contextlib
import email.mime.text
import enum
import functools
import pathlib
import pickle
import pickletools
import re
import smtplib
import socket
import sys
import threading
import tkinter.messagebox
import traceback
import zlib


# Dump all of tkinter's constants into the local namespace.
from tkinter.constants import *


# Import custom modules in a way that an IDE will recognize them.
with Resource.load('affinity.py'), \
     Resource.load('threadbox.py'), \
     Resource.load('safetkinter.py'):
    try:
        from .safetkinter import *
    except SystemError:
        from safetkinter import *
    try:
        from . import threadbox
    except SystemError:
        import threadbox


# Patch the messagebox module to use a thread-safe version of Message.
tkinter.messagebox.Message = Message


# Create an enumeration to represents various program states.
Status = enum.Enum('Status', 'mail_label login_button connection_error')


def event_handler(method):
    """Allow command/event handlers to be marked and written more easily."""
    @functools.wraps(method)
    def wrapper(self, event=None):
        nonlocal none_counter
        none_counter += event is None
        method(self)
        # print('Commands handled:', none_counter)
    none_counter = 0
    return wrapper


class SMTPClient(Frame):

    """Widget for sending emails through a GUI program in Python."""

    TITLE = 'SMTP Mail Sender'

    AT_ICON = 'at.ico'
    HELP_ICON = 'help.ico'
    HELP_TEXT = 'get_help.txt'

    IS_TARGET = r'\A(\w|\.)+@\w+\.\w+\Z'
    IS_SUBJECT = r'\S+'
    IS_MESSAGE = r'\S+'

    @classmethod
    def main(cls):
        """Create an application containing a single SMTPClient widget."""
        root = cls.create_application_root()
        cls.create_windows_bindings(root)
        cls.attach_window_icon(root)
        cls.setup_class_instance(root)
        root.mainloop()

    @classmethod
    def create_application_root(cls):
        """Create and configure the main application window."""
        root = Tk()
        root.title(cls.TITLE)
        # root.resizable(False, False)
        root.minsize(275, 200)
        root.option_add('*tearOff', FALSE)
        return root

    @classmethod
    def create_windows_bindings(cls, root):
        """Change some global bindings to work like Microsoft products."""
        root.bind_all('<Control-Key-a>', cls.handle_control_a)
        root.bind_all('<Control-Key-A>', cls.handle_control_a)
        root.bind_class('Text', '<Control-Key-/>', lambda event: 'break')

    @staticmethod
    def handle_control_a(event):
        """Treat Control-A as would be expected on a Windows system."""
        widget = event.widget
        if isinstance(widget, Entry):
            widget.selection_range(0, END)
            return 'break'
        if isinstance(widget, Text):
            widget.tag_add(SEL, 1.0, END + '-1c')
            return 'break'

    @classmethod
    def attach_window_icon(cls, root):
        """Generate and use the icon in the window's corner."""
        with Resource.load(cls.AT_ICON) as handle:
            root.iconbitmap(handle)

    @classmethod
    def setup_class_instance(cls, root):
        """Build a SMTPClient instance that expects to be have size changes."""
        widget = cls(root)
        widget.grid(row=0, column=0, sticky=NSEW)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

    def __init__(self, master=None, **kw):
        """Initialize the SMTPClient instance and configure for operation."""
        super().__init__(master, **kw)
        self.__tk = self.capture_root()
        self.create_bindings()
        self.__to_entry = self.__subject_entry = self.__message_text = \
            self.__quit_button = self.__send_button = self.__from_label = \
            self.__to_label = self.__subject_label = self.__login_button = \
            self.__grip = None
        self.create_widgets()
        self.configure_grid()
        self.__data_handler = DataHandler()
        self.__connector = self.after_idle(self.try_connect)

    def destroy(self):
        """Cancel the connection system before closing."""
        self.after_cancel(self.__connector)
        super().destroy()

    def capture_root(self):
        """Capture the rook (Tk instance) of this application."""
        widget = self.master
        while not isinstance(widget, Tk):
            widget = widget.master
        return widget

    def create_bindings(self):
        """Bind the frame to any events that it will need to handle."""
        self.__tk.bind('<Control-Key-h>', self.handle_help)
        self.__tk.bind('<Control-Key-H>', self.handle_help)
        self.__tk.bind('<Control-Key-l>', self.handle_login)
        self.__tk.bind('<Control-Key-L>', self.handle_login)
        self.__tk.bind('<Key>', self.handle_update)
        self.__tk.bind('<Return>', self.handle_send)

    def create_widgets(self):
        """Create all the widgets that will be placed in this frame."""
        self.__to_entry = Entry(self)
        self.__subject_entry = Entry(self)
        self.__message_text = Text(self)
        self.__quit_button = Button(
            self,
            text='Quit',
            command=self.__tk.destroy
        )
        self.__send_button = Button(
            self,
            text='Send',
            command=self.do_send,
            state=DISABLED
        )
        self.__from_label = Label(self, text='From:')
        self.__to_label = Label(self, text='To:')
        self.__subject_label = Label(self, text='Subject:')
        self.__login_button = Button(
            self,
            text='Login Before Sending',
            command=self.do_login
        )
        self.__grip = Sizegrip(self)

    def configure_grid(self):
        """Place all widgets on the grid in their respective locations."""
        pad = dict(padx=5, pady=5)
        self.__from_label.grid(row=0, column=0, **pad)
        self.__login_button.grid(
            row=0,
            column=1,
            columnspan=4,
            sticky=EW,
            **pad
        )
        self.__to_label.grid(row=1, column=0, **pad)
        self.__to_entry.grid(row=1, column=1, columnspan=4, sticky=EW, **pad)
        self.__subject_label.grid(row=2, column=0, **pad)
        self.__subject_entry.grid(
            row=2,
            column=1,
            columnspan=4,
            sticky=EW,
            **pad
        )
        self.__message_text.grid(
            row=3,
            column=0,
            columnspan=5,
            sticky=NSEW,
            **pad
        )
        self.__quit_button.grid(row=4, column=2, **pad)
        self.__send_button.grid(row=4, column=3, **pad)
        self.__grip.grid(row=4, column=4, sticky=SE, **pad)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(1, weight=1)

    @event_handler
    def handle_help(self):
        """Open the help window and show a message for the user."""
        with Resource.load(self.HELP_TEXT) as text, \
                Resource.load(self.HELP_ICON) as icon:
            TextViewer.load(self.__tk, text, icon)

    @event_handler
    def handle_login(self):
        """Decide if the user should be able to login to the server."""
        if self.current_status == Status.login_button:
            self.do_login()

    @event_handler
    def handle_update(self):
        """Decide if it should be possible to send an e-mail or not."""
        to = self.__to_entry.get()
        subject = self.__subject_entry.get()
        message = self.__message_text.get(0.0, END)
        self.__send_button['state'] = ACTIVE if self.is_target(to) \
            and self.is_subject(subject) \
            and self.is_message(message) \
            and self.__data_handler.is_connected else DISABLED

    @classmethod
    def is_target(cls, text):
        """Determine if this is an acceptable e-mail address."""
        return bool(re.search(cls.IS_TARGET, text))

    @classmethod
    def is_subject(cls, text):
        """Determine if this is an acceptable subject line."""
        return bool(re.search(cls.IS_SUBJECT, text))

    @classmethod
    def is_message(cls, text):
        """Determine if this is an acceptable message to send."""
        return bool(re.search(cls.IS_MESSAGE, text))

    @event_handler
    def handle_send(self):
        """Send only if the application is ready to do so."""
        if self.__send_button['state'] == ACTIVE:
            self.do_send()

    def do_send(self):
        """Start a thread to send an e-mail in an asynchronous method."""
        threading.Thread(target=self.send_thread).start()

    @threadbox.MetaBox.thread
    def send_thread(self):
        """Try to send an e-mail and display the results of the attempt."""
        destination = self.__to_entry.get()
        try:
            self.__data_handler.send(
                destination,
                self.__subject_entry.get(),
                self.__message_text.get(0.0, END)
            )
        except:
            tkinter.messagebox.showerror(
                'Error',
                'An exception has occurred.\n'
                'Continue for more details.',
                master=self
            )
            TextViewer(self.__tk, 'Traceback', traceback.format_exc())
        else:
            tkinter.messagebox.showinfo(
                'Success',
                'The message was sent successfully to {}.'.format(destination),
                master=self
            )

    @property
    def current_status(self):
        """Find out what status the program currently is in."""
        return (Status.connection_error
                if not self.__data_handler.is_connected else
                Status.login_button
                if not self.__data_handler.is_logged_in else
                Status.mail_label)

    def do_login(self):
        """Open the login window and also the user to supply credentials."""
        with Resource.load('login.ico') as icon:
            LoginWindow(self.__tk, icon, self.__data_handler)
        self.__login_button['text'] = self.__data_handler.username or ''
        self.refresh()

    def try_connect(self):
        """Repeatedly try to connect to the server every 0.6 seconds."""
        if not self.__data_handler.is_connected:
            self.__data_handler.try_connect(self.refresh)
        self.__connector = self.after(600, self.try_connect)

    def refresh(self, is_connected=False):
        """Let the user know if there is a connection to the server."""
        if is_connected:
            tkinter.messagebox.showinfo(
                'Server',
                'Your connection is live!',
                master=self
            )


class TextViewer(Toplevel):

    """Widget designed to show text in a window."""

    BACKGROUND = '#FFFFFF'
    FOREGROUND = '#000000'
    WIDTH = 800
    HEIGHT = 600
    X_OFFSET = 10
    Y_OFFSET = 10

    @classmethod
    def load(cls, parent, text_handle, icon_handle):
        """Open a TextViewer with information loaded from a file."""
        with text_handle.open('rt') as file:
            title, *text = map(str.strip, file)
        cls(parent, title, '\n'.join(text), icon_handle)

    def __init__(self, parent, title, text, icon_handle=None):
        """Initializes the window for the reader to see its contents."""
        super().__init__(parent, borderwidth=5)
        if icon_handle is not None:
            self.iconbitmap(icon_handle)
        self.geometry('={}x{}+{}+{}'.format(
            self.WIDTH,
            self.HEIGHT,
            parent.winfo_rootx() + self.X_OFFSET,
            parent.winfo_rooty() + self.Y_OFFSET
        ))
        self.__frame_text = self.__frame_buttons = self.__okay_button = \
            self.__scrollbar_view = self.__text_view = None
        self.create_widgets()
        self.configure_widgets()
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.okay)
        self.__text_view.focus_set()
        self.create_bindings()
        self.__text_view.insert(0.0, text)
        self.__text_view['state'] = DISABLED
        self.wait_window()

    def create_widgets(self):
        """Populates the window with the widgets that will be needed."""
        self.__frame_text = Frame(self, relief=SUNKEN, height=700)
        self.__frame_buttons = Frame(self)
        self.__okay_button = Button(
            self.__frame_buttons,
            text='Close',
            command=self.okay,
            takefocus=FALSE
        )
        self.__scrollbar_view = Scrollbar(
            self.__frame_text,
            orient=VERTICAL,
            takefocus=FALSE
        )
        self.__text_view = Text(
            self.__frame_text,
            wrap=WORD,
            fg=self.FOREGROUND,
            bg=self.BACKGROUND,
            highlightthickness=0
        )

    def configure_widgets(self):
        """Put them in their proper places throughout the layout."""
        self.__scrollbar_view['command'] = self.__text_view.yview
        self.__text_view['yscrollcommand'] = self.__scrollbar_view.set
        self.__okay_button.pack()
        self.__scrollbar_view.pack(side=RIGHT, fill=Y)
        self.__text_view.pack(side=LEFT, expand=TRUE, fill=BOTH)
        self.__frame_buttons.pack(side=BOTTOM, fill=X)
        self.__frame_text.pack(side=TOP, expand=TRUE, fill=BOTH)

    @event_handler
    def okay(self):
        """Close the window."""
        self.destroy()

    def create_bindings(self):
        """Allow the window to respond to certain events."""
        self.bind('<Return>', self.okay)
        self.bind('<Escape>', self.okay)


class DataHandler:

    """Handler for communications with a SMTP server."""

    HOST = 'smtp.gmail.com'
    PORT = 587

    __slots__ = (
        '__is_logged_in',
        '__is_connected',
        '__server',
        '__username',
        '__password'
    )

    def __init__(self):
        """Initializes the DataHandler instance's various flags."""
        self.__is_logged_in = False
        self.__is_connected = self.__server = self.__username = \
            self.__password = None
        self.__cancel_connection()

    @property
    def is_logged_in(self):
        """Checks whether or not the instance believes it is logged in."""
        return self.__is_logged_in

    @property
    def is_connected(self):
        """Checks whether or not the instance believes it is connected."""
        return self.__is_connected

    @staticmethod
    def __check_string(value, name):
        """Verify that the string has a value type and value."""
        if not isinstance(value, str):
            raise TypeError('{} must be of type str'.format(name))
        if not value:
            raise ValueError('{} must not be an empty string'.format(name))

    def __get_username(self):
        """Retrieves the value of the username."""
        return self.__username

    def __set_username(self, text):
        """Validates the username and sets its value."""
        self.__check_string(text, 'username')
        self.__username = text

    username = property(
        __get_username,
        __set_username,
        None,
        'Sets value of username.'
    )

    def __set_password(self, text):
        """Validates the password and sets its value."""
        self.__check_string(text, 'password')
        self.__password = text

    password = property(fset=__set_password, doc='Sets value of password.')

    def try_connect(self, callback=lambda status: None):
        """Attempt to connect to the pre-configured server address."""
        threading.Thread(target=self.__connect, args=(callback,)).start()

    def __connect(self, callback):
        """Connect to the server in an asynchronous fashion."""
        try:
            self.__server = smtplib.SMTP(self.HOST, self.PORT, None, 1)
        except (smtplib.SMTPException, socket.gaierror, socket.timeout):
            self.__cancel_connection()
        else:
            self.__is_connected = True
        callback(self.__is_connected)

    def send(self, destination, subject, message):
        """Try to send an e-mail with the provided information."""
        if self.__server is None:
            raise RuntimeError('cannot send without a valid connection')
        packet = email.mime.text.MIMEText(message)
        packet['From'] = self.__username
        packet['To'] = destination
        packet['Subject'] = subject
        self.__server.starttls()
        self.__server.login(self.__username, self.__password)
        self.__server.send_message(packet)
        self.__finish()

    def __cancel_connection(self):
        """Reset the is_connected and server attributes to default values."""
        self.__is_connected = False
        self.__server = None

    def validate_credentials(self):
        """Verify if the saved credentials are correct or not."""
        if self.__server is None:
            raise RuntimeError('cannot validate without a working connection')
        try:
            self.__server.starttls()
            self.__server.login(self.__username, self.__password)
        except smtplib.SMTPException:
            self.__is_logged_in = False
        else:
            self.__is_logged_in = True
        finally:
            self.__finish()
        return self.__is_logged_in

    def __finish(self):
        """Finish the conversation taking place with the server."""
        self.__server.close()
        self.__cancel_connection()


class Dialog(Toplevel):

    """Generic widget that should be used as a base class."""

    X_OFFSET = 50
    Y_OFFSET = 50

    def __init__(self, parent, title=None, icon_handle=None):
        """Initialize a Dialog window that takes focus away from the parent."""
        super().__init__(parent)
        self.withdraw()
        if icon_handle is not None:
            self.iconbitmap(icon_handle)
        if parent.winfo_viewable():
            self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.grid(sticky=NSEW, padx=5, pady=5)
        self.okay_button = self.cancel_button = None
        self.button_box()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        parent = self.parent
        if parent is not None:
            self.geometry('+{}+{}'.format(
                parent.winfo_rootx() + self.X_OFFSET,
                parent.winfo_rooty() + self.Y_OFFSET
            ))
        self.deiconify()
        self.initial_focus.focus_set()
        try:
            self.wait_visibility()
        except tkinter.TclError:
            pass
        else:
            self.grab_set()
            self.wait_window(self)

    def destroy(self):
        """Destruct the Dialog window."""
        self.initial_focus = None
        super().destroy()

    def body(self, master):
        """Create the body of this Dialog window."""
        pass

    def button_box(self):
        """Create the standard buttons and Dialog bindings."""
        box = Frame(self)
        self.okay_button = Button(
            box,
            text='Okay',
            width=10,
            command=self.okay,
            default=ACTIVE
        )
        self.okay_button.grid(row=0, column=0, padx=5, pady=5)
        self.cancel_button = Button(
            box,
            text='Cancel',
            width=10,
            command=self.cancel
        )
        self.cancel_button.grid(row=0, column=1, padx=5, pady=5)
        self.bind('<Return>', self.okay)
        self.bind('<Escape>', self.cancel)
        box.grid()

    @event_handler
    def okay(self):
        """Validate and apply the changes made by this Dialog."""
        if self.validate():
            self.withdraw()
            self.update_idletasks()
            try:
                self.apply()
            finally:
                self.cancel()
        else:
            self.initial_focus.focus_set()

    @event_handler
    def cancel(self):
        """Close the Dialog window and return to its parent."""
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

    def validate(self):
        """Verify that the Dialog is in a valid state."""
        return True

    @staticmethod
    def apply():
        """Make any changes the Dialog wishes to accomplish."""
        pass


class LoginWindow(Dialog):

    """Widget to allow easy process for supplying credentials."""

    TITLE = 'E-mail Login'
    WIDTH = 45
    MASK = '*'

    def __init__(self, parent, icon_handle, data_handler):
        """Initialize the dialog with the necessary information."""
        self.__data_handler = data_handler
        super().__init__(parent, self.TITLE, icon_handle)
        self.__username_label = self.__password_label = self.__username = \
            self.__password = None

    def body(self, master):
        """Create all the different widgets needed for the body."""
        self.__username_label = Label(master, text='Gmail Address:')
        self.__password_label = Label(master, text='Password:')
        self.__username = Entry(master, width=self.WIDTH)
        self.__password = Entry(master, width=self.WIDTH, show=self.MASK)
        self.__username_label.grid(row=0, column=0, padx=5, pady=5, sticky=E)
        self.__username.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
        self.__password_label.grid(row=1, column=0, padx=5, pady=5, sticky=E)
        self.__password.grid(row=1, column=1, padx=5, pady=5, sticky=EW)
        self.bind('<Key>', self.refresh)
        return self.__username

    def button_box(self):
        """Create the button box and change okay button's options."""
        super().button_box()
        self.okay_button.configure(state=DISABLED, text='Login')

    @event_handler
    def refresh(self):
        """Perform a soft validation for the username and password."""
        username = self.__username.get()
        password = self.__password.get()
        valid = re.search(r'\A(\w|\.)+@gmail\.com\Z', username) is not None \
            and len(password) > 3
        self.okay_button['state'] = ACTIVE if valid else DISABLED

    def validate(self):
        """Attempt to validate username and password with the server."""
        self.__data_handler.username = self.__username.get()
        self.__data_handler.password = self.__password.get()
        valid = self.__data_handler.validate_credentials()
        if valid:
            tkinter.messagebox.showinfo(
                'Login Success',
                'The credentials were accepted.\n'
                'You are now logged in!',
                master=self
            )
        else:
            self.__password.delete(0, END)
            tkinter.messagebox.showerror(
                'Login Error',
                'This username/password combination was not accepted.\n'
                'Please try again.',
                master=self
            )
        return valid


if __name__ == '__main__':
    SMTPClient.main()