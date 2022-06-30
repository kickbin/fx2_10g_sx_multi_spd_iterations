#Programmer Reference online
#http://kms.spirentcom.com/CSC/STC%20Programmers%20Ref_WebHelp/WebHelp/Default.htm
#Object references online
#http://kms.spirentcom.com/CSC/pabtech/stc-automation-html/index.htm

# This loads the TestCenter library.
# STC python version 5.32
import sys
from StcPython import StcPython

stc = StcPython()

def gen_port_handles(hProject, port_1_loc, port_2_loc):
    hPort_1 = stc.create("port", under=hProject, location=port_1_loc, useDefaultHost=False)
    hPort_2 = stc.create("port", under=hProject, location=port_2_loc, useDefaultHost=False)
    return hPort_1, hPort_2

def specify_port_options(SPEED, AUTO_NEG, DIAG_LOOPBACK):
    # Configure physical interface.
    port_options_dict =  {"PerformanceMode":"STC_MGIG", \
        "AdvertiseIEEE":"TRUE", \
           "AdvertiseNBASET":"TRUE", \
           "AutoNegotiation": "TRUE", \
           "FlowControl":"FALSE", \
           "Duplex":"FULL", \
           "IgnoreLinkStatus":"FALSE", \
           "DataPathMode":"NORMAL", \
           "Mtu":"1500", \
           "ForwardErrorCorrection":"TRUE", \
           "CustomFecChange":"0", \
           "CustomFecMode":"KR_FEC"}

    if SPEED == "ALL_SPEEDS":
        port_options_dict["AlternateSpeeds"] = "SPEED_10G SPEED_5G SPEED_2500M SPEED_1G SPEED_100M"
    elif SPEED == "SPEED_10G":
        port_options_dict["AlternateSpeeds"] = "SPEED_10G"
    elif SPEED == "SPEED_5G":
        port_options_dict["AlternateSpeeds"] = "SPEED_5G"
    elif SPEED == "SPEED_2500M":
        port_options_dict["AlternateSpeeds"] = "SPEED_2500M"
    elif SPEED == "SPEED_1G":
        port_options_dict["AlternateSpeeds"] = "SPEED_1G"
    elif SPEED == "SPEED_100M":
        port_options_dict["AlternateSpeeds"] = "SPEED_100M"

    if AUTO_NEG == False:
        port_options_dict["AutoNegotiation"] = False
        
    if DIAG_LOOPBACK == True:
        port_options_dict["DataPathMode"] = "LOCAL_LOOPBACK"
    
    return port_options_dict

def config_ports(port_options_dict, port_1, port_2):
    print(port_1)
    print(port_2)
    hfx2_10G_port_1 = stc.create("Ethernet10GigFiber", under=port_1, **port_options_dict)
    hfx2_10G_port_2 = stc.create("Ethernet10GigFiber", under=port_2, **port_options_dict)         

    stc.config(port_1, **{"ActivePhy-targets": [hfx2_10G_port_1]})
    stc.config(port_2, **{"ActivePhy-targets": [hfx2_10G_port_2]})
    
def show_ports_line_spd_status(port_1, port_2):
    ports = [port_1, port_2]
    for port in ports:
        hPortSpeed = stc.get(port, "activephy")
        line_speed_status = stc.get(hPortSpeed, "LineSpeedStatus")
        print(port, " Line Speed Status: ", line_speed_status)

def gen_stream_handles(port_1):
    # Create a stream block.
    print("Configuring stream block ...")
    hStreamBlock = stc.create("streamBlock", under=port_1, insertSig=True, \
                              frameConfig="", frameLengthMode="FIXED", \
                              maxFrameLength=1200, FixedFrameLength=256)

    # Add an EthernetII Protocol Data Unit (PDU).
    print("Adding headers")
    hEthernet  = stc.create("ethernet:EthernetII", under=hStreamBlock, \
                            name="sb1_eth", srcMac="00:00:20:00:00:00", \
                            dstMac="00:00:00:00:00:00")

    # Use modifier to generate multiple streams.
    print("Creating Modifier on Stream Block ...")
    hRangeModifier = stc.create("RangeModifier", \
          under=hStreamBlock, \
          ModifierMode="DECR", \
          Mask="00:00:FF:FF:FF:FF", \
          StepValue="00:00:00:00:00:01", \
          Data="00:00:10:10:00:01", \
          RecycleCount=20, \
          RepeatCount=0, \
          DataType="NATIVE", \
          EnableStream=True, \
          Offset=0, \
          OffsetReference="sb1_eth.dstMac")

    # Display stream block information.
    print("\n\nStreamBlock information")

    dictStreamBlockInfo = stc.perform("StreamBlockGetInfo", StreamBlock=hStreamBlock)

    for szName in dictStreamBlockInfo:
        print("\t", {szName}, "\t", {dictStreamBlockInfo[szName]})

    print("\n\n")

    return hStreamBlock, hEthernet, hRangeModifier

def config_generator(hGenerator):
    hGeneratorConfig = stc.get(hGenerator, "children-GeneratorConfig")

    stc.config(hGeneratorConfig, \
              DurationMode="CONTINUOUS", \
              BurstSize=1, \
              Duration=30, \
              LoadMode="FIXED", \
              FixedLoad=90, \
              LoadUnit="PERCENT_LINE_RATE", \
              SchedulingMode="PORT_BASED")

def gen_result_handles(hProject):
        # Subscribe to realtime results.
        print("Subscribe to results")
        hAnaResults = stc.subscribe(Parent=hProject, \
                    ConfigType="Analyzer", \
                    resulttype="AnalyzerPortResults",  \
                    filenameprefix="Analyzer_Port_Results")

        hGenResults = stc.subscribe(Parent=hProject, \
                    ConfigType="Generator", \
                    resulttype="GeneratorPortResults",  \
                    filenameprefix="Generator_Port_Counter", \
                    Interval=2)
        return hAnaResults, hGenResults

def perf_start_gen_ana(hAnalyzer, hGenerator):
    # Start the analyzer and generator.
    print("Start Analyzer")
    stc.perform("AnalyzerStart", AnalyzerList=hAnalyzer)
    print( "Current analyzer state ", {stc.get(hAnalyzer, "state")} )

    print("Start Generator")
    stc.perform("GeneratorStart", GeneratorList=hGenerator)
    print( "Current generator state",  {stc.get(hGenerator, "state")} )

def display_traffic_results(hGenerator, hAnalyzer):
    # Example of Direct-Descendant Notation ( DDN ) syntax. ( DDN starts with an object reference )
    print( "Frames Counts:" )
    print( "\tSignature Frames Generated:", {stc.get("%s.GeneratorPortResults(1)" % hGenerator, "GeneratorSigFrameCount")} )
    print("\tSignature Frames Received: ", {stc.get("%s.AnalyzerPortResults(1)" % hAnalyzer, "sigFrameCount")})
    print("\tFrames Generated:", {stc.get("%s.GeneratorPortResults(1)" % hGenerator, "GeneratorFrameCount")})
    print("\tTotal Frames Received: ", {stc.get("%s.AnalyzerPortResults(1)" % hAnalyzer, "TotalFrameCount")})
    print( "\tTotal frame count: ", {stc.get("%s.AnalyzerPortResults(1)" % hAnalyzer, "totalFrameCount")} )
    print("\tFCS frame count: ", {stc.get("%s.AnalyzerPortResults(1)" % hAnalyzer, "FcsErrorFrameCount")})
    print( "\tDropped frames: ", {stc.get("%s.AnalyzerPortResults(1)" % hAnalyzer, "DroppedFrameCount")} )

def config_gen_ana_start_stop_streams(port_1, port_2, hProject):
    # Retrieve the generator and analyzer objects.
    hGenerator = stc.get(port_1, "children-Generator")
    hAnalyzer = stc.get(port_2, "children-Analyzer")

    # Required
    hStreamBlock, hEthernet, hRangeModifier = gen_stream_handles(port_1)

    # Configure generator.
    config_generator(hGenerator)
    print("Configuring Generator")
    
    # Analyzer Configuration.
    print("Configuring Analyzer")
    hAnalyzerConfig = stc.get(hAnalyzer, "children-AnalyzerConfig")

    # Apply the configuration.
    print("Apply configuration")
    stc.apply()

    # generate result handles
    hAnaResults, hGenResults = gen_result_handles(hProject)

    # Apply configuration.
    print("Apply configuration")
    stc.apply()

    # Save the configuration as an XML file. Can be imported into the GUI.
    # print("\nSave configuration as an XML file.")
    # stc.perform("SaveAsXml")

    # Start Generator and Analyzer
    perf_start_gen_ana(hAnalyzer, hGenerator)

    print("Wait 5 seconds ...")
    stc.sleep(5)

    print("Wait until generator stops ...")
    test_state = stc.waitUntilComplete(timeout=100)

    print( "Current analyzer state ", {stc.get(hAnalyzer, "state")} )
    print( "Current generator state ", {stc.get(hGenerator, "state")} )
    print("Stop Analyzer")

    # Stop the generator.
    stc.perform("GeneratorStop", GeneratorList=hGenerator)

    # Stop the analyzer.
    stc.perform("AnalyzerStop", AnalyzerList=hAnalyzer)

    # Display some statistics.
    display_traffic_results(hGenerator, hAnalyzer)

    # results clear
    stc.perform("ResultsClearView", ResultDataSet=hGenResults)
    stc.perform("ResultsClearView", ResultDataSet=hAnaResults)

    return hGenResults, hAnaResults


def init():
    SPEEDS = ["ALL_SPEEDS", "SPEED_10G", "SPEED_5G", "SPEED_2500M", "SPEED_1G", "SPEED_100M"]
    # AlternateSpeeds options: "ALL_SPEEDS" "SPEED_10G" "SPEED_5G" "SPEED_2500M" "SPEED_1G" "SPEED_100M" 
    AUTO_NEG = True
    # AUTO_NEG options: "True" "False"
    DIAG_LOOPBACK = False
    # DIAG_LOOPBACK options: "True" "False"

    stc.log("INFO", "Starting Test")
    # This line will show the TestCenter commands on stdout
    stc.config("automationoptions", logto="stdout", loglevel="ERROR")
    #loglevel options: "INFO", "WARN", "ERROR", "FATAL"
    # Retrieve and display the current API version.
    print("SpirentTestCenter system version:\t", {stc.get("system1", "version")})

    # Physical topology
    #szChassisIp = "10.226.44.151"
    szChassisIp = "10.108.8.20"
    port_1_loc = "//%s/%s/%s" % ( szChassisIp, 3, 13) # Only 2 ports are used to test, reserve 4 ports to change mode
    port_2_loc = "//%s/%s/%s" % ( szChassisIp, 3, 14)

    # Create the root project object
    print("Creating project ...")
    hProject = stc.create("project")

    # Create port handles
    print("Creating ports ...")
    hPort_1, hPort_2 = gen_port_handles(hProject, port_1_loc, port_2_loc)
    
    for SPEED in SPEEDS:
        # configure port speed
        port_options_dict = specify_port_options(SPEED, AUTO_NEG, DIAG_LOOPBACK)
    
        # FX2-10G-S16 port config
        config_ports(port_options_dict, hPort_1, hPort_2)

        # Attach ports.
        # Connects to chassis, reserves ports and sets up port mappings all in one step.
        # By default, connects to all previously created ports.
        print("Attaching ports ", {port_1_loc}, {port_2_loc})
        stc.perform("AttachPorts")

        # Apply the configuration.
        print("Apply configuration")
        stc.apply()

        # Show interface line speed status
        show_ports_line_spd_status(hPort_1, hPort_2)
        
        # config Generator, Analyzer and start stop streams
        hGenResults, hAnaResults = config_gen_ana_start_stop_streams(hPort_1, hPort_2, hProject)

    # Unsubscribe from results
    print( "Unsubscribe results ..." )
    stc.unsubscribe(hAnaResults)
    stc.unsubscribe(hGenResults)

    # Disconnect from chassis, release ports, and reset configuration.
    print( "Release ports and disconnect from chassis" )
    stc.perform('chassisDisconnectAll')
    stc.perform('resetConfig', createnewtestsessionid=0)

    # Delete configuration
    print( "Deleting project" )
    stc.delete(hProject)

    stc.log("INFO", "Ending Test")

    # return test_state