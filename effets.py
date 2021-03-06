#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gevent

from gevent.pool import Group
from time import sleep, time

# from audio_functions import *
from dmx_functions import *
from data.equipment import *
from data.colors import *


class Effets():
    """
        dans cette classe se trouvent tous les effets -- qui sont finalement des séquences.
        autant la musique tourne en tâche de fond sans souci (via VLC.py), autant le
        DMX non. ce dernier sert donc de base temporelle, dans cette classe.

        un effet comprend une suite d'effets lumières via la classe DMX (importée depuis dmx_functions).

        remarque : les blackout se font en début de séquence, pour être sûr qu'ils soient pris en compte
        (le problème de les mettre en fin de séquence, c'est que le dmx_streamer risque d'être killé avant
        que la trame blackout ne soit partie).

    """

    def __init__(self, arduino_dmx, arduino_ultrasonics, arduino_lotus):
        self.arduino_dmx = arduino_dmx
        self.arduino_ultrasonics = arduino_ultrasonics
        self.arduino_lotus = arduino_lotus




    def sequence(self, ref_thread_events, dmx_frame, priority_dmx_frame, dmx_streamer):
        """
            la séquence principale des sirènes, chronologiquement par effets-lumière.

            voir le premier appel de la méthode add_effect pour un aperçu de ses différents paramètres.

            vous pouvez travailler à partir d'un temps spécifique en modifiant la constante STARTING_TIME à autre chose que 0.

        """


        """
        ####################################################################
                        QUELQUES FONCTIONS POUR LA SÉQUENCE
        ####################################################################
        """

        def add_simple_effect(equipment, starting_time, effect, effect_args):
            """
                more transparency than add_effect, more freedom for users' calls.
            """
            starting_time += STARTING_TIME

            equipment.append(
                gevent.spawn_later(starting_time, effect, dmx_frame, *effect_args)
            )


        def add_effect(equipment, starting_time, dmx_channels, effect, effect_args, overrided_channels=None, repeat=1):
            """
                gère, en plus de add_simple_effet :
                    - le niveau de priorité du dmx
                    - le nombre de fois qu'il faut exécuter la fonction
                    - la possibilité de passer en bloc une liste de canaux plutôt qu'un seul
                    - ...
            """
            starting_time += STARTING_TIME

            # s'il y a des canaux à haut niveau de priorité on démarre un thread prioritaire pour le flux DMX
            if overrided_channels:
                override_duration = effect_args[0]  # un peu pourri comme pratique
                current_dmx_frame = priority_dmx_frame
                overrider = gevent.spawn_later(starting_time, dmx_high_priority_overrider, current_dmx_frame, overrided_channels, True)
            # sinon c'est le flux DMX normal
            else:    
                current_dmx_frame = dmx_frame

            # génère un thread par canal, avec des répétitions de fonctions si demandé
            for times in range(repeat):
                for channel in dmx_channels:        
                    equipment.append(
                        gevent.spawn_later(starting_time, effect, current_dmx_frame, channel, *effect_args)
                    )
        
            # s'il y avait des canaux à haut niveau de priorité on arrête le thread prioritaire pour le flux DMX
            if overrided_channels:
                overrider = gevent.spawn_later(starting_time + override_duration, dmx_high_priority_overrider, current_dmx_frame, overrided_channels, False)


        def laughs_effect(start_time, times_number, interval):
            for i in range(1, times_number):
                add_effect(main_gevent, start_time,            [PARLED_1.r, PARLED_1.b], fade_up_down, [1, 20, 255, 4])
                add_effect(main_gevent, start_time+interval,   [PARLED_2.r, PARLED_2.b], fade_up_down, [1, 20, 255, 4])
                add_effect(main_gevent, start_time+interval*2, [PARLED_3.r, PARLED_3.b], fade_up_down, [1, 20, 255, 4])
                add_effect(main_gevent, start_time+interval*3, [PARLED_4.r, PARLED_4.b], fade_up_down, [1, 20, 255, 4])
                start_time = start_time + interval*4

        def petite_explosion(starting_time):
            """
                à reprendre !
            """
            add_effect(main_gevent, 20.3,   [PARLED_2.r], fade_up_down, [0.8, 50, 255, 6])
            add_effect(main_gevent, 20.5,   [PARLED_2.b], fade_up, [1, 0, 255, 2])
            add_effect(main_gevent, 21.5,   [PARLED_2.r, PARLED_2.b], fade_down, [0.5, 255, 0, 4])



        def effet_palpitation_graduelle(dmx_frame, starting_time, duration, int_dep, int_fin):
            """
                palpite de plus en plus vite.
            """
            d = starting_time
            interval = int_dep
            dec = (int_dep - int_fin)/20
            while starting_time-d < duration:
                add_effect(main_gevent, starting_time,  PARLED_ALL.r, fade_up_down, [interval, 30, 100, 4])
                add_effect(main_gevent, starting_time,  PARLED_ALL.b, fade_up_down, [interval, 50, 255, 4])
                starting_time = starting_time + interval + 0.3
                interval = interval - dec

        """
        ####################################################################
                        CONFIG & INITIALISATION DE LA SÉQUENCE
        ####################################################################
        """

        STARTING_TIME = 0  # used for debugging

        
        main_gevent = []

        add_simple_effect(main_gevent, 3,    constants, [BANDEAU_LED.rgb, [0, 0, 0]])


        """
        ####################################################################
                    LA SÉQUENCE i.e. tous les effets à la suite
        ####################################################################
        """
        ## INTRO
        add_effect(
            equipment=main_gevent,
            starting_time=0,
            dmx_channels=[PARLED_1.b, PARLED_2.b],
            effect=fade_up,
            effect_args=[0.2, 0, 255, 6],
            overrided_channels=None,    # optional
            repeat=1                    # optional
        )
        add_effect(main_gevent, 0.5,    [PARLED_1.r, PARLED_1.g, PARLED_2.r, PARLED_2.g], fade_up, [1, 0, 255, 4])
        add_effect(main_gevent, 1.2,    PARLED_1.rgb+PARLED_2.rgb, fade_up_down, [0.2, 0, 255, 8, 3.8])

        add_effect(main_gevent, 0,      [PARLED_3.r, PARLED_4.r], fade_up_down, [0.8, 0, 255, 8])
        add_effect(main_gevent, 0,      [PARLED_3.b, PARLED_4.b], fade_up_down, [0.8, 0, 255, 8])        
        add_effect(main_gevent, 3,      PARLED_3.rgb+PARLED_4.rgb, fade_up_down, [0.3, 0, 255, 8, 2])
        
        add_effect(main_gevent, 5,      PARLED_1.rgb+PARLED_2.rgb, fade_down, [2, 255, 0, 2])
        add_effect(main_gevent, 5,      PARLED_3.rgb+PARLED_4.rgb, fade_down, [2.2, 255, 0, 2])

        

        ## premières paroles (VIOLET)
        add_effect(main_gevent, 9.2,    [PARLED_1.r, PARLED_1.b], fade_up, [0.3, 0, 50, 4])
        add_effect(main_gevent, 9.5,    [PARLED_1.r, PARLED_1.b], fade_up_down, [2.9, 50, 255, 4], repeat=3)
        add_effect(main_gevent, 19,     [PARLED_1.r, PARLED_1.b], fade_down, [0.2, 50, 0, 4])
        add_effect(main_gevent, 13.2,   [PARLED_2.r, PARLED_2.b], fade_up, [0.3, 0, 50, 4])
        add_effect(main_gevent, 13.5,   [PARLED_2.r, PARLED_2.b], fade_up_down, [2, 50, 255, 4], repeat=2)
        add_effect(main_gevent, 18,     [PARLED_2.r, PARLED_2.b], fade_down, [1, 50, 0, 2])


        # HARPE - suite des paroles (BLEU)
        add_effect(main_gevent, 19,     [PARLED_1.b], fade_up,   [1, 0, 255, 2])
        add_effect(main_gevent, 20,     [PARLED_1.b], fade_down, [0.5, 255, 0, 5])
        add_effect(main_gevent, 25,     [PARLED_1.b], fade_up,   [1, 0, 255, 2])
        add_effect(main_gevent, 26,     [PARLED_1.b], fade_down, [0.5, 255, 0, 4])
        
        add_effect(main_gevent, 20.5,   [PARLED_2.b], fade_up,   [1, 0, 255, 2])
        add_effect(main_gevent, 21.5,   [PARLED_2.b], fade_down, [0.5, 255, 0, 4])
        add_effect(main_gevent, 26.5,   [PARLED_2.b], fade_up,   [1, 0, 255, 4])
        add_effect(main_gevent, 27.5,   [PARLED_2.b], fade_down, [0.5, 255, 0, 2])

        add_effect(main_gevent, 22,     [PARLED_3.b], fade_up,   [1, 0, 255, 2])
        add_effect(main_gevent, 23,     [PARLED_3.b], fade_down, [0.5, 255, 0, 4])

        add_effect(main_gevent, 23.5,   [PARLED_4.b], fade_up,   [1, 0, 255, 2])
        add_effect(main_gevent, 24.5,   [PARLED_4.b], fade_down, [0.5, 255, 0, 4])

        ## fade up down rose
        add_effect(main_gevent, 28,     PARLED_ALL.r+PARLED_ALL.b, fade_up,   [2, 0,255, 4])
        add_effect(main_gevent, 30,     PARLED_ALL.r+PARLED_ALL.b, fade_down, [0.4, 255, 0, 4])

        ## éclat rouge
        add_effect(main_gevent, 30.5,   PARLED_ALL.r, fade_up,   [1, 0,255, 2])
        add_effect(main_gevent, 31.5,   PARLED_ALL.r, fade_down, [1, 255,0, 2])
        add_simple_effect(main_gevent, 32.5, constants, [[PARLED_1.r, PARLED_1.b], [0, 0]])


        ## RIRES (GOUTTES VIOLET + RIRES JAUNES)
        laughs_effect(32.5, 14, 0.5)

        # simule des rires, qui prennent le dessus sur tout le reste (via le paramètre override_param)
        add_effect(main_gevent, 40.4,   [PARLED_1.r, PARLED_1.g], fade_up_down, [1, 0, 255, 6], overrided_channels=PARLED_1.rgb)
        add_effect(main_gevent, 48,     [PARLED_1.r, PARLED_1.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_1.rgb)
        add_effect(main_gevent, 51.4,   [PARLED_1.r, PARLED_1.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_1.rgb)

        add_effect(main_gevent, 41.4,   [PARLED_2.r, PARLED_2.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_2.rgb)
        add_effect(main_gevent, 55.5,   [PARLED_2.r, PARLED_2.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_2.rgb)
        add_effect(main_gevent, 56,     [PARLED_2.r, PARLED_2.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_2.rgb)

        add_effect(main_gevent, 46.5,   [PARLED_3.r, PARLED_3.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_3.rgb)
        add_effect(main_gevent, 52.5,   [PARLED_3.r, PARLED_3.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_3.rgb)
        
        add_effect(main_gevent, 50.4,   [PARLED_4.r, PARLED_4.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_4.rgb)
        add_effect(main_gevent, 53.5,   [PARLED_4.r, PARLED_4.g], fade_up_down, [1, 0, 266, 6], overrided_channels=PARLED_4.rgb)
        
        add_effect(main_gevent, 60.5,   [PARLED_1.r, PARLED_1.b], fade_up_down, [0.5, 20, 255, 4])
        add_effect(main_gevent, 61,     [PARLED_2.r, PARLED_2.b], fade_up_down, [0.5, 20, 255, 4])

        ## PREMIER CRI
        add_simple_effect(main_gevent, 61.7, strobe, [PARLED_ALL.rgb, 1, 100, 255, 15])
        add_effect(main_gevent, 62.8,   PARLED_ALL.rgb, fade_up, [0.2, 0,255, 2])
        add_effect(main_gevent, 63,     PARLED_ALL.rgb, fade_down, [2, 255, 0, 2])
        add_simple_effect(main_gevent, 65.1, strobe, [PARLED_ALL.rgb, 2, 100, 255, 15])

        add_effect(main_gevent, 67.5,  PARLED_ALL.r + PARLED_ALL.b, fade_up_down, [1, 20, 255, 4])


        ## DÉBUT CRESCENDO FINAL
        effet_palpitation_graduelle(dmx_frame, 72.5, 23, 1.5, 0.3)
        
        ## clignotements rouges rapides
        add_effect(main_gevent, 78,     [PARLED_1.r], fade_up_down, [0.2, 0, 255, 6, 6.95], overrided_channels=PARLED_1.rgb)
        add_effect(main_gevent, 78,     [PARLED_2.r], fade_up_down, [0.3, 0, 255, 6, 6.95], overrided_channels=PARLED_2.rgb)
        add_effect(main_gevent, 78,     [PARLED_3.r], fade_up_down, [0.4, 0, 255, 6, 5.95], overrided_channels=PARLED_3.rgb)
        add_effect(main_gevent, 78,     [PARLED_4.r], fade_up_down, [0.5, 0, 255, 6, 5.95], overrided_channels=PARLED_4.rgb)


        # ## vortex final (majoritairement blanc)
        add_effect(main_gevent, 96,     PARLED_3.rgb + PARLED_4.rgb, fade_down, [0.5, 255, 0, 2])

        add_effect(main_gevent, 95.5,   PARLED_1.rgb + PARLED_2.rgb, fade_up_down, [0.2, 0, 255, 8, 2.9])
        add_effect(main_gevent, 97,     PARLED_3.rgb + PARLED_4.rgb, fade_up_down, [0.3, 0, 255, 1.5])

        add_effect(main_gevent, 98.5,   PARLED_1.rgb + PARLED_2.rgb, fade_down, [2, 255, 0, 2])
        add_effect(main_gevent, 98.5,   PARLED_3.rgb + PARLED_4.rgb, fade_down, [2, 255, 0, 2])

        # on laisse le temps au dmx de s'écouler proprement
        main_gevent.append(gevent.spawn_later(99, gevent.sleep(2)))
        
        while (len(gevent.joinall(main_gevent, timeout=0)) != len(main_gevent)) :
            sleep(.00001)
            # pc_1000 = gevent.spawn( fade_up_down, PC_1000, 1, 0, 150, 6, 0)
            # gevent.joinall([pc_1000])

        print ("SEQUENCE: DMX TERMINÉ")

        sleep(2)
        # dmx_streamer.kill()

        print('SEQUENCE: fin séquence sirènes')


    def battement_de_coeur(self, ref_thread_events, dmx_frame, priority_dmx_frame, dmx_streamer, level):
        """
            battement de coeur lorsque des visiteurs sont entrés.
            - level 1 lorsqu'ils sont loins
            - level 2 lorsqu'ils sont proches

        """
        pause_between_heartbeat = 1  # in seconds
        
        while not(ref_thread_events.thread_lotus.must_start_sequence):
            g_bandeau = gevent.spawn_later(
                0,
                intro_battement, dmx_frame, BANDEAU_LED.r,
                ref_must_start_sequence=ref_thread_events.thread_lotus.must_start_sequence,
                level=level
            )
            while(len(gevent.joinall([g_bandeau], timeout=0)) != len([g_bandeau])):
                if ref_thread_events.thread_lotus.must_start_sequence:
                    break
            
            # équivalent de la fonction time.sleep() mais interruptible en cas de lotus touché
            tic = time()
            while (time() - tic < pause_between_heartbeat) and not(ref_thread_events.thread_lotus.must_start_sequence):
                sleep(.00001)
                

        # dmx_streamer.kill()

            


    def sequence_intro_caverne(self, ref_thread_events, dmx_frame, priority_dmx_frame, dmx_streamer):#, dmx_frame, priority_dmx_frame):

        # g_parled_1 = gevent.spawn(constants, dmx_frame, PARLED_1.rgb, bleu_turquoise)
        # g_parled_2 = gevent.spawn(constants, dmx_frame, PARLED_2.rgb, bleu_turquoise)
        # g_parled_3 = gevent.spawn(constants, dmx_frame, PARLED_3.rgb, bleu_turquoise)
        # g_parled_4 = gevent.spawn(constants, dmx_frame, PARLED_4.rgb, bleu_turquoise)



        while not(ref_thread_events.thread_ultrasonics.visitors_detected):
            g_bandeau = gevent.spawn(intro_lotus_oscillations, dmx_frame, BANDEAU_LED.r)
            gevent.joinall([g_bandeau])



        # g_parled_1.kill()
        # g_parled_2.kill()
        # g_parled_3.kill()
        # g_parled_4.kill()
        try:
            g_bandeau.kill()
        except exc_info():
            print exc_info()
            print exc_info()[-1].tb_lineno
            pass

        # dmx_streamer.kill()


        