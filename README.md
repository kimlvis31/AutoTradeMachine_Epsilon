# AutoTradeMachine_Epsilon

This is the fifth version of the **Auto Trade Machine** project.

The main aspects of this version are:  

**1. Local Process Status Tracking**  
    Added real-time tracking of process and IPC performance.  
  
**2. Logger Class**  
    Introduced a logger class that can handle formatted console print and record printed messages.  
  
**3. IPC DAR (Data Acquisition Request)**
Alongside PRD (Pre-registered Data) and FAR (Function Activation Request), a new IPC mechanism is added.  

Previously, a process could acquire data from other processes only by reading PRD entries in shared memory, or by sending a FAR and waiting for a response.  

A problem with PRD is that it is a shared memory. Compared to updating a local memory, shared-memory update can be extremely slow, and this becomes a problem when frequent data updates are required.  
    
DAR is introduced to resolve this. Instead of dispatching a new data to the shared-memory every time it is updated, the local memory is updated. And only when a request is received via IPC, it is then automatically dispatched within the IPC module processing. When the data needs to be transferred every time it is updated, DAR would not be suitable. But when only the latest data is required (for instance, average IPC processing speed), DAR can avoid any unnecessary computation.  
  
**4. Market Data Import And Local Management Process Evaluation**  
- *Market Data Import*  
    Upon program initialization, all of market data is imported from three Binance markets (SPOT, Futures USD-M, and Futures COIN-M). Their symbols are locally saved to use as the key when storing any asset data (such as each asset's first kline timestamp).  
  
- *First Kline Timestamp Identification*  
    The *first kline* is the earliest kline retrievable for a symbol, and defines the lower bound of the historical range. When asset data is read, the 'first kline timestamp' is checked; if not recorded locally, the symbol is queued for identification.  
  
- *WebSocket Kline Stream*  
    Due to the REST API rate limits, it is impossible to fetch klines data of all assets at every kline interval (also painfully slow). To keep track of 'all assets' on the market in real-time, this version experiments with Binance *WebSocket* streams. After subscribing once, continuous kline updates arrive without additional requests.  
  
- *Local Data Management Process*  
    The combined dataset of several thousand assets (SPOT, Futures USD-M, and COIN-M combined) can be massive. Below is an example for BTC/USDT (Futures USD-M).  
    - First Kline Timestamp: 1567965420 (2019-09-09 02:57 UTC)  
    - Current Day Timestamp: 1762214400 (2025-11-04 00:00 UTC)  
    - Kline Interval: 1m, 5m, 1h  
    - Number of Klines: ~3.2M, ~640K, ~53.3K  
    - Number of Parameters Per Kline Data: ~10 (This can vary depending on what the program requires and wants to keep track of, but generally includes timestamp, OHLC prices, volumes, etc.)  
    - Data Size Per Parameter Per Kline: 4 Bytes (Assuming float32)  
    - Total Size of Klines Data:  
        1m: 3.2M *10*4 = ~128 MB (512 GB for 4000 assets)  
        5m: 640K *10*4 = ~ 26 MB (104 GB for 4000 assets)  
        1h: 53.3K*10*4 = ~2.1 MB (8.4 GB for 4000 assets)  
    Details can vary. Not all assets are introduced into the market for this long and data can be saved in different formats and precisions. However, from the example above, it can easily be seen how heavy asset data can become. One sure thing is that trying to fetch all this data once program launches is impractical, and the best way to do this would be to build a local database, and load data that is only needed for view and analysis onto the RAM. In order to store such large volume of data, this version experimented with a framework for database management.  
  
**5. New GUI Components**  
    Added the following user interface elements:  
        - Selection Box  
        - Table View  
  
**6. [REMOVED] Page Metadata Files**  
    I realized that there isn't really a point in keeping the pages initialization data in external files. First it comes with a risk of initialization process crash if edited inappropriately (In fact, why would it be needed to be edited by non-developers anyways?). The major reason is that an activation of a GUI object will often trigger a unique function, which needs to be defined somewhere. Defining such functions with external files can be very difficult to debug, but more importantly, same with the objects themselves, they should not be edited by non-developers. Leaving such room for program compromise is absolutely unwanted.
  
**7. [REMOVED] GUI Framework**  
    'CTGO_Alpha.py' and 'GUIObjects_Alpha.py' have been replaced with:  
        - 'ATM_Epsilon_tkinterExtension.py'  
        - 'ATM_Epsilon_tkinterExtension_MS.py'  
    I thought these names better reflect their true purpose as **Tkinter extension modules**.  
  
---

### 🗓️ Project Duration
**October 2023 – March 2024**

---

### 📄 Document Info
**Last Updated:** November 4th, 2025  
**Author:** Bumsu Kim  
**Email:**  kimlvis31@gmail.com  
