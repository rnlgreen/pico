#Train
#New train function with hopefully better logic
def train(num_carriages=5, colour_list=[], iterations=0): # pylint: disable=dangerous-default-value
    """train sequence"""
    #log.status(f"Starting with {num_carriages}, {colour_list}, {iterations}")
    now_running("train")

    #limit_run is a flag to say whether we are running a limited number of passes
    limit_run = iterations > 0

    if len(colour_list) == 0:
        for c in range(num_carriages):
            colour_list += [wheel(int(255*c/num_carriages))]

    log.status(f"Colour list: {colour_list}")

    #progression is a counter to say how far the train has travelled
    progression = numPixels
    t = millis()

    while not (stop or (limit_run and iterations == 0)) and not (stop_after > 0 and time.time() > stop_after):
        check_mqtt()
        carriage_length = int(numPixels / num_carriages)
        progression += 1
        for i in range(numPixels):
            if progression > i:
                carriage_no = int((progression - i) / carriage_length) % len(colour_list)
                mycolour = colour_list[carriage_no]
                r, g, b, _ = list_to_rgb(mycolour)
            else:
                r, g, b = [0, 0, 0]

            set_pixel(i, r, g, b)
        strip.show()
        if stop:
            break
        #Only pico5 controls the brightness using the light sensor
        if master and auto:
            if ticks_diff(t, millis()) > 10000:
                manage_lights()
                t = millis()
        time.sleep(0.75 * dyndelay / 1000)
    #set_all(0, 0, 0)
    now_running("None")

