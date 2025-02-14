import unittest
import numpy as np
import pandas as pd
from tkinter import Tk, StringVar
from unittest.mock import MagicMock, patch

from Hysteresis.data.processing import *
from Hysteresis.gui.main_window import MainApp


class TestNormalizationClose(unittest.TestCase):

    def setUp(self):
        '''
        Prepare the data simulating real hysteresis loops:
        1) Use sigmoids as initial data.
        2) Add random noise to simulate errors.
        3) Create pairs of columns representing the two branches of a loop.
        '''
        # Create a Tkinter window
        self.root = Tk()

        # Creates an instance of MainApp, simulating the main application
        self.app = MainApp(self.root)

        # Set up a simulated logger for the app
        self.app.logger = MagicMock()

        # Data simulation
        x = np.linspace(-1, 1, 200)  # Magnetic fiedl
        np.random.seed(69420)        # For reproducibility
        noise = np.random.normal(0, 0.0005, size=x.shape)  # Gaussian error

        # Creation of the two branches of the hysteresis loop
        # The sigmoid function is used to simulate the hysteresis loop
        # The noise is added to simulate the experimental error
        # The last term is a linear trend to simulate a drift
        # The -0.003 is due to the fact that the loop is always closed at one of the extreme points.
        y_up = 0.025 + 0.015 * (1 / (1 + np.exp(-10 * (x-0.25)))) + noise + (0.003*x - 0.003)
        y_dw = 0.025 + 0.015 * (1 / (1 + np.exp( 10 * (x-0.25))))[::-1] + noise[::-1]

        # Create the DataFrame
        self.df = pd.DataFrame({"FieldUp": x, "Up": y_up,
                                "FieldDw": x, "Down": y_dw})
        self.app.dataframes = [self.df]

        # Simulate the selection of the columns
        self.selected_pairs = [
            (MagicMock(get=lambda: "File 1"), None, MagicMock(get=lambda: "Up")),
            (MagicMock(get=lambda: "File 1"), None, MagicMock(get=lambda: "Down"))
        ]

        self.plot_data = MagicMock()       # Mock for plot function
        self.app.count_plot = [0]          # Flag for plot counter
        self.app.plot_customizations = {}  # Optional plot customizations

    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        '''
        self.root.destroy() # Destroy Tkinter window

    def test_normalization(self):
        '''
        Testing the norm() function:
        1) Check that normalization is applied correctly.
        2) Check that the branches have a combined width of approximately 1.
        3) Check that the loop is centered at zero.
        4) Check that the logger records the normalization operation.
        '''

        # Call function to test
        norm(self.plot_data, self.app.count_plot, self.selected_pairs,
             self.app.dataframes, self.app.plot_customizations, self.app.logger)

        # Retrieve the normalized data
        normalized_up = self.app.dataframes[0]["Up"].values
        normalized_dw = self.app.dataframes[0]["Down"].values

        # Verify that the loop is centered at zero
        mean_up = np.mean(normalized_up)
        mean_dw = np.mean(normalized_dw)
        self.assertAlmostEqual(mean_up + mean_dw, 0, places=1)

        # Verify that the branches have a combined width of approximately 1
        ampiezza_up = abs(np.mean(normalized_up[:5])  + np.mean(normalized_dw[:5]))/2
        ampiezza_dw = abs(np.mean(normalized_up[-5:]) + np.mean(normalized_dw[-5:]))/2
        self.assertAlmostEqual(ampiezza_up , 1, places=1)
        self.assertAlmostEqual(ampiezza_dw, 1, places=1)

        # Verify that the logger records the normalization operation
        self.app.logger.info.assert_any_call("Normalizzazione applicata alle colonne Down.")
        self.app.logger.info.assert_any_call("Normalizzazione applicata alle colonne Up.")
    
    @patch("Hysteresis.data.processing.messagebox.showinfo")
    def test_applay_close(self, mock_showinfo):
        '''
        Testing the applay_close() function:
        1) Check that the close operation is applied correctly.
        2) Check that the message box works correctly.
        3) Check that the logger records the normalization operation.
        '''

        # Initial data
        up = self.app.dataframes[0]["Up"].values
        dw = self.app.dataframes[0]["Down"].values
        initial_gap = abs(up[0] - dw[0])
        
        # User choice
        file_choice      = StringVar(value=f"File 1")
        selected_columns = {"Up": StringVar(value="True"), "Down":StringVar(value="True")}

        # Call function to test
        apply_close(self.plot_data, file_choice, selected_columns, self.app.count_plot,
                    self.selected_pairs, self.app.dataframes, self.app.plot_customizations,
                    self.app.logger)
        
        # Result
        up = self.app.dataframes[0]["Up"].values
        dw = self.app.dataframes[0]["Down"].values
        final_gap = abs(up[0] - dw[0])

        # Verify close loop
        self.assertLess(final_gap, initial_gap)

        # Verify that the logger records the closure operation
        self.app.logger.info.assert_any_call("Chiusura del ciclo applicata a Up.")
        self.app.logger.info.assert_any_call("Chiusura del ciclo applicata a Down.")

        # Check that the success message is displayed
        mock_showinfo.assert_any_call("Successo", "Operazione applicata su File 1!")
    
    @patch("Hysteresis.data.processing.messagebox.showerror")
    def test_close_no_selection(self, mock_showerror):
        ''' Test error for no file selection
        '''
        apply_close(self.plot_data, StringVar(value=''), {}, self.app.count_plot,
                self.selected_pairs, self.app.dataframes, self.app.plot_customizations,
                 self.app.logger)
        mock_showerror.assert_called_once_with('Errore', 'Devi selezionare un file!')
    
    @patch("Hysteresis.data.processing.messagebox.showerror")
    def test_close_no_selection(self, mock_showerror):
        ''' Test error for no columns selection
        '''
        apply_close(self.plot_data, StringVar(value='File 1'), {}, self.app.count_plot,
                self.selected_pairs, self.app.dataframes, self.app.plot_customizations,
                 self.app.logger)
        mock_showerror.assert_called_once_with("Errore", "Devi selezionare la coppia di dati che crea il ciclo")
    


class TestCloseFunction(unittest.TestCase):

    def setUp(self):
        ''' Test for close window
        '''
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window

        # Simulate a example dataFrame
        self.df1 = MagicMock(columns=["FieldUp", "Up", "FieldDw", "Down"])
        self.df2 = MagicMock(columns=["H1", "V1", "H2", "V2", "H3", "V3"])
        self.dataframes = [self.df1, self.df2]

        # Other important paramether
        self.logger = MagicMock()
        self.plot_data = MagicMock()
        self.count_plot = [0]
        self.selected_pairs = []
        self.plot_customizations = {}

    @patch("Hysteresis.data.processing.tk.Toplevel")
    @patch("Hysteresis.data.processing.tk.OptionMenu")
    @patch("Hysteresis.data.processing.tk.Button")
    @patch("Hysteresis.data.processing.apply_close")
    def test_close_ui_elements(self, mock_apply_close, mock_button, mock_optionmenu, mock_toplevel):
        '''
        Verify that:
        1) The window is created.
        2) The drop-down menu for selecting files is present.
        3) The "Apply" button calls apply_close with the correct parameters.
        '''
        # Simulate toplevel window
        mock_window = MagicMock()
        mock_toplevel.return_value = mock_window

        # Simulate drop-down menù
        mock_optionmenu.return_value = MagicMock()

        # Call the function to test
        close(self.root, self.plot_data, self.count_plot, self.selected_pairs,
              self.dataframes, self.plot_customizations, self.logger)

        # Verify that the window has been created
        mock_toplevel.assert_called_once_with(self.root)
        mock_window.title.assert_called_once_with("Chiudi loop")

        # Verify that the drop-down menù has been created
        mock_optionmenu.assert_called_once()

        # Simulates pressing the button
        args, kwargs = mock_button.call_args
        self.assertIn("command", kwargs)

        # Simulate the command execution to verify that apply_close is called
        if "command" in kwargs:
            kwargs["command"]()

        mock_apply_close.assert_called_once()