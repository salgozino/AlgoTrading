#import getpass
import utils.PMY_REST as pmy

def select_tickers_pase():
    opcion = 0
    while (opcion < 1) or (opcion > 2):
        print("Futuros con pase disponibles para operar:\n * 1: Rofex \n * 2: Dolar")
        opcion = int(input("Elija la opcion deseada: "))
    
    if opcion == 2:
        instrumentos = pmy.instrumentos()

        index = 0
        valid_instruments = []
        for i, instrumento in enumerate(instrumentos['instruments']):
            tickers_names = instrumento['instrumentId']['symbol']
            if ('DO' in  tickers_names) and (tickers_names.endswith("9") or tickers_names.endswith("0")) and ("DOP" not in tickers_names):
                print('Opcion {}: {}'.format(index,tickers_names)) 
                valid_instruments.append(tickers_names)
                index+=1
        ticker_corto = ''
        ticker_largo = ''
        while ticker_corto == '':
            try:
                inp = int(input("Elija el ticker de corto plazo: "))
            except KeyboardInterrupt:
                break
            except:
                print('Error, por favor ingrese un número entero.')
                inp = -1
                
            if (inp < 0) or (inp > len(valid_instruments)):
                print('La opcion ingresada no es correcta. Intentelo de nuevo')
            else:
                ticker_corto = valid_instruments[inp]
                print('El ticker corto elegido fue: ', ticker_corto)
        while ticker_largo == '':
            try:
                inp = int(input("Elija el ticker de largo plazo: "))
            except KeyboardInterrupt:
                break
            except:
                print('Error, por favor ingrese un número entero.')
                inp = -1
            if (inp < 0) or (inp > len(valid_instruments)):
                print('La opcion ingresada no es correcta. Intentelo de nuevo')
            else:
                ticker_largo = valid_instruments[inp]
                print('El ticker largo elegido fue: ', ticker_largo)
        abbr_to_num = {'Ene':'01','Feb':'02','Mar':'03','Abr':'04','May':'05','Jun':'06','Jul':'07','Ago':'08','Sep':'09','Oct':'10','Nov':'11','Dic':'12'}
        mes_corto = ticker_corto[2:5]
        mes_largo = ticker_largo[2:5]
        mes_corto = abbr_to_num[mes_corto]
        mes_largo = abbr_to_num[mes_largo]

        ticker_pase = 'DOP ' + mes_corto + '/' + mes_largo + ' 19'
        print('Su ticker de pase es:', ticker_pase)
    else:
        ticker_corto = 'RFX20Jun19'
        ticker_largo = 'RFX20Sep19'
        ticker_pase = "RFXP 06/09 19"
        print('El ticker corto elegido fue: ', ticker_corto)
        print('El ticker largo elegido fue: ', ticker_largo)
        print('Su ticker de pase es:', ticker_pase)
    return ticker_corto,ticker_largo,ticker_pase

def select_ticker():
        #Set a thread with the strategy to implement, in one specific ticker, or more than one.
        opcion = 0
        while (opcion < 1) or (opcion > 2):
            print("Tickers disponibles para operar:\n * 1: RFX20Sep19\n * 2: DoAgo19")
            opcion = int(input("Elija la opcion deseada: "))
            if opcion == 1:
                ticker = 'RFX20Sep19'
            elif opcion == 2:
                ticker = 'DoAgo19'
                
            
        max_loss = 0
        while max_loss <20:
            try:
                max_loss = int(input("Ingrese la máxima perdida que tolera (numero entero mayor o igual a 20): "))
            except:
                print("Valor incorrecto, ingrese un número entero mayor o igual a 20.")
        return ticker, max_loss
        
def ask_login_credentials():
    entorno = 4
    while entorno > 1 or entorno < 0:
        try:
            print("Modos Disponibles\n * 1 Modo Simulacion con Remarkets\n * 0 Modo PRODUCCIÓN")
            entorno = int(input("Indique el modo en el que desea operar (0 o 1): "))
        except ValueError:
            print("Ingrese un valor adecuado.")
    
    if entorno == 0:
        user = input("Ingrese su usuario: ")
        password = input('Password:')
        account = user
        db = 'rofex.db'
    elif entorno == 1:
#        user = input("Ingrese su usuario: ")
#        password = input('Password:')
#        account = input("Ingrese su cuenta: ")
        user = 'salgozino898'
        password = 'oeofsZ2*'
        account = 'REM898'
        db = 'remarkets.db'

    return user, password, account, entorno,db
    
