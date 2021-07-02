def optimizationSetup(self):

        optimizationSetup = QtWidgets.QDialog()
        ui = Ui_optimizationSetup()
        ui.setupUi(optimizationSetup)
        self.setWindow(optimizationSetup)

        ui.layout_generation_setup.hide()
        ui.performance_selector.hide()
        ui.electrical_setup.hide()
        ui.thermal_setup.hide()

        def next_clicked():
            if not ui.run_options.isHidden(): # Run Options Visible
                if ui.option_2.isChecked():
                    ui.performance_selector.show()
                    ui.run_options.hide()
                elif ui.option_1.isChecked():
                    ui.layout_generation_setup.show()
                    ui.run_options.hide()
                    ui.next_btn.setText("Finish")
                elif ui.option_3.isChecked():
                    ui.layout_generation_setup.show()
                    ui.run_options.hide()
            elif not ui.layout_generation_setup.isHidden():  # Layout Generation Visible
                if ui.option_1.isChecked():
                    print("CLOSED!")
                    #optimizationSetup.close()
                elif ui.option_2.isChecked() or ui.option_3.isChecked():
                    ui.layout_generation_setup.hide()
                    ui.performance_selector.show()
            elif not ui.performance_selector.isHidden():  # Performance Selector Visible
                if ui.activate_electrical_2.isChecked():
                    ui.electrical_setup.show()
                    ui.performance_selector.hide()
                    if not ui.activate_thermal_2.isChecked():
                        ui.next_btn.setText("Finish")
                elif ui.activate_thermal_2.isChecked():
                    ui.thermal_setup.show()
                    ui.performance_selector.hide()
                    ui.next_btn.setText("Finish")
            elif not ui.electrical_setup.isHidden():  # Electrical Setup Visible
                if ui.activate_thermal_2.isChecked():
                    ui.thermal_setup.show()
                    ui.electrical_setup.hide()
                    ui.next_btn.setText("Finish")
                else:
                    print("CLOSED!")
                    #optimizationSetup.close()
            elif not ui.thermal_setup.isHidden():  # Thermal Setup Visible
                print("CLOSED!")
                #optimizationSetup.close()


        def back_clicked():
            ui.next_btn.setText("Next")
            if not ui.run_options.isHidden(): # Run Options Visible
                pass
            elif not ui.layout_generation_setup.isHidden():  # Layout Generation Visible
                ui.layout_generation_setup.hide()
                ui.run_options.show()
            elif not ui.performance_selector.isHidden():  # Performance Selector Visible
                if ui.option_3.isChecked():
                    ui.layout_generation_setup.show()
                    ui.performance_selector.hide()
                elif ui.option_2.isChecked():
                    ui.run_options.show()
                    ui.performance_selector.hide()
            elif not ui.electrical_setup.isHidden():  # Electrical Setup Visible
                ui.performance_selector.show()
                ui.electrical_setup.hide()
            elif not ui.thermal_setup.isHidden():  # Thermal Setup Visible
                if ui.activate_electrical_2.isChecked():
                    ui.electrical_setup.show()
                    ui.thermal_setup.hide()
                else:
                    ui.performance_selector.show()
                    ui.thermal_setup.hide()
        
        ui.next_btn.pressed.connect(next_clicked)
        ui.back_btn.pressed.connect(back_clicked)

        optimizationSetup.show()


    def createMacro(self, figure):

        createMacro = QtWidgets.QDialog()
        ui = Ui_createMacro()
        ui.setupUi(createMacro)
        self.setWindow(createMacro)

        scene = QtWidgets.QGraphicsScene()
        ui.graphicsView.setScene(scene)

        def option0():
            ui.layout_generation_setup.show()
            ui.performance_selector.hide()
            ui.electrical_setup.hide()
            ui.thermal_setup.hide()

        def option1():
            ui.layout_generation_setup.hide()
            ui.performance_selector.show()
            if ui.activate_electrical.isChecked():
                ui.electrical_setup.show()
            else:
                ui.electrical_setup.hide()
            if ui.activate_thermal.isChecked():
                ui.thermal_setup.show()
            else:
                ui.thermal_setup.hide()

        def option2():
            ui.layout_generation_setup.show()
            ui.performance_selector.show()
            if ui.activate_electrical.isChecked():
                ui.electrical_setup.show()
            else:
                ui.electrical_setup.hide()
            if ui.activate_thermal.isChecked():
                ui.thermal_setup.show()
            else:
                ui.thermal_setup.hide()

        def activateElectrical():
            if ui.activate_electrical.isChecked():
                ui.electrical_setup.hide()
            else:
                ui.electrical_setup.show()

        def activateThermal():
            if ui.activate_thermal.isChecked():
                ui.thermal_setup.hide()
            else:
                ui.thermal_setup.show()

        # Ensures that the frame doesn't move the objects when they're hidden
        def retainSize(widget):
            sp_retain = widget.sizePolicy()
            sp_retain.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(sp_retain)
        
        retainSize(ui.layout_generation_setup)
        retainSize(ui.performance_selector)
        retainSize(ui.electrical_setup)
        retainSize(ui.thermal_setup)

        # Hide necessary layouts
        ui.layout_generation_setup.hide()
        ui.performance_selector.hide()
        ui.electrical_setup.hide()
        ui.thermal_setup.hide()

        ui.option_1.pressed.connect(option0)
        ui.option_2.pressed.connect(option1)
        ui.option_3.pressed.connect(option2)

        ui.activate_electrical.pressed.connect(activateElectrical)
        ui.activate_thermal.pressed.connect(activateThermal)


        figure.set_figheight(4)  # Adjusts the size of the Figure
        figure.set_figwidth(4)
        canvas = FigureCanvas(figure)
        scene.addWidget(canvas)

        createMacro.show()