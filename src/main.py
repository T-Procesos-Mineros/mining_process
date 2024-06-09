from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

class ScenarioScreen(Screen):
    def __init__(self, scenario_num, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text=f'This is Scenario {scenario_num}'))

class MiningApp(App):
    def build(self):
        root = BoxLayout(orientation='horizontal')
        
        # Create a vertical box layout for the buttons
        button_layout = BoxLayout(orientation='vertical', size_hint=(0.2, 1))
        
        # Create the screen manager
        self.screen_manager = ScreenManager()
        
        # Add scenarios as screens
        for i in range(9):
            screen = ScenarioScreen(scenario_num=i+1, name=f'scenario_{i+1}')
            self.screen_manager.add_widget(screen)
        
        # Add buttons to the button layout
        for i in range(9):
            button = Button(text=f'scenario {i + 1}')
            button.bind(on_press=self.change_scenario)
            button_layout.add_widget(button)
        
        # Add the button layout and screen manager to the root layout
        root.add_widget(button_layout)
        root.add_widget(self.screen_manager)
        
        # Set the default screen to scenario 1
        self.screen_manager.current = 'scenario_1'
        
        return root

    def change_scenario(self, instance):
        scenario_name = instance.text.lower().replace(' ', '_')
        self.screen_manager.current = scenario_name

if __name__ == '__main__':
    MiningApp().run()