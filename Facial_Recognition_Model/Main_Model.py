import Astro
import pickle
import face_recognition
import os
import shutil
import re
import numpy as np
import multiprocessing as mp
from multiprocessing import Process
cache_img = True
err_log = []

#Just a helper method, carry on...
def getDir(filePath:str):
    if "/" not in filePath and "\\" not in filePath:
        return "./"
    regex = re.compile(r"\/")
    filePath = regex.split(filePath)
    return "/".join(filePath[:-1])+"/"

def getFileName(filePath:str):
    if "/" not in filePath and "\\" not in filePath:
        return filePath
    regex = re.compile(r"\/")
    filePath = regex.split(filePath)
    return filePath[-1]

def prepDir(fileDir:str):
    if fileDir[-1] == "/" or fileDir[-1] =="\\": fileDir = fileDir[:-1]
    if not os.path.isdir(fileDir):
        os.makedirs(fileDir)
    
def makePickle(directory:str, file_name:str, pickle_obj):
    regex = re.compile(r"\.")
    file_name_no_extension = regex.split(file_name)[0]
    prepDir(directory)
    with open("{0}{1}.dat".format(directory,file_name_no_extension),"wb") as f:
        pickle.dump(pickle_obj,f)

def printErr(msg:str):
    if len(err_log) == 0 : return    
    print(msg)
    while len(err_log) != 0:
        print("\t{}".format(err_log.pop()))
    
 
class Master_Model:
    """Model trained to find all astronauts. Contains methods for adding astronauts to
        model,searching a picture for astronauts, or searching all pictures in a 
        directory for any of the astronauts in the model. Must be in a directory
        with a folder for storing pickled face_recognition models. Any .dat files 
        in that directory will be added to the model.
        
        Model takes a LONG TIME to train and to search an image for faces. This will hopefully be improved soon, but for testing puposes only run on a subset of astronauts"""


    def __init__(self, train_dir:str, astro_pickle_dir:str, num_threads = 1):
        """Class constructor for Main_Model.

        PARAM: train_dir:str = directory containing pictures of all astronauts to be added to model. Picture files must follow the following naming convention: 
                <first name>_[<middle name>_]<last name>&<nationality>.jpg

            astro_pickle_dir:str = Directory in which face_recognition model objects will be flattened and saved as .dat files. Note that any .dat files in this directory will be added to model

            num_threads:int = Number of threads to be used by the model (not yet implemented)"""
        prepDir(astro_pickle_dir)
        self.astro_pickle_dir = astro_pickle_dir
        self.num_threads = abs(num_threads)
        self.known_faces = self.itemizeKnown()
        self.found_faces = {}
        self.img_cache = {}
        self.train(train_dir)
        if os.path.exists("./img_cache/img_cache.dat"):
            with open("./img_cache/img_cache.dat",'rb') as f:
                self.img_cache = pickle.load(f)


    def train(self,train_dir:str):     
        """Function adds astronaut objects to model for every image in the given directory and trains the astonaut object to recognize the face in the image. If an image in the directory already has a corresponding .dat file in astro_pickle_dir, it will be ignored.

        Param: train_dir: Directory in which all images to be trained on are stored. Images must follow this naming convention:
                <first name>_[<middle name>_]<last name>&<nationality>.jpg"""
        print("Training on all images in {0} using {1} threads".format(train_dir,self.num_threads))
        semaphore = mp.Semaphore(max(1,self.num_threads-1))
        processes = []
        lock = mp.Lock()
        for filename in os.listdir(train_dir):
            if filename.split(".")[-1] != "jpg": continue
            lock.acquire()
            print("Training on image:", filename)
            lock.release()
            a = self.astroInit(filename)
            if a == None : continue
            if a.filename in self.known_faces :
                print("\tModel has already been trained on",filename)
                continue
            semaphore.acquire()
            p = Process(target = self.addAstro, args = ("{0}{1}".format(train_dir,filename), semaphore,lock))
            processes.append(p)
            p.start()
        for proc in processes:
            proc.join()
            

            
    def addAstro(self,astronaut,sem:mp.Semaphore, lock:mp.Lock):
        """File adds given astronaut object or picture to model.
        
        Parameter:
        astronaut = Can by of type Astro.Astronaut or str (in which case it should be a file path). If it is of type Astro.Astronaut, astronaut will be directly added to the model. If it is a filepath, an astronaut object will be created, trained on the image, and added to the model. Filepath must follow naming conventions outlined in Master_Model.train()
            """
        if type(astronaut) == Astro.Astronaut:
            astronaut.saveData(self.astro_pickle_dir)
            self.known_faces[astronaut.filename] = astronaut.facialData
        if type(astronaut) == str:
            a = self.astroInit(astronaut)
            if(a==None):
               sem.release() 
               return
            if a.filename in self.known_faces:
                lock.acquire()
                print("\tModel has already been trained on",astronaut)
                lock.release()
                sem.release()
                return
            a.trainModel(astronaut,lock)
            if type(a.facialData) == np.ndarray:
                a.saveData(self.astro_pickle_dir)
                self.known_faces[a.filename] = a.facialData
            sem.release()

#    def addAstros(self, astros:list):
#        """Same behavior as addAstro, but works on a list of filepaths or astronaut objects"""
#        for a in astros:
#            self.addAstro(a)
    
    def astroInit(self, filepath):
        #helper method, nothing to see here...
        regex_noPath = re.compile(r'\/')
        regex_nc = re.compile(r"&")
        regex_names = re.compile(r"_")
        regex_no_dot = re.compile(r"\.")
        filename = regex_noPath.split(filepath)[-1]
        name_country = regex_nc.split(filename)
        ident = regex_names.split(name_country[0])
        country = regex_no_dot.split(name_country[1])[0]
        if "cropped" in ident:
            ident.remove("cropped")
        if len(ident)==3:
            fName, lName, mName = ident    
            return Astro.Astronaut(country,fName,lName,mName)
        elif len(ident)==2:
            fName, lName = ident
            return Astro.Astronaut(country, fName, lName)
        else:
            print("\tERROR: Incorrectly formatted file name: {}\n\tFiles must be named <first name>_<lastname>&country.jpg".format(filename))
            print("\tFile will be ignored")
            return None

    def loadAstro(self, filePath):
        #helper method, nothing to see here...
        a = self.astroInit(filePath)
        directory = getDir(filePath)
        if a == None:
            return None
        a.loadData(directory)
        return a

    def findFaces(self,img_path:str, sem:mp.Semaphore, lock:mp.Lock):
        """Method searches image for astronaut faces

        Parameters:
        img_path:str = path of image to search for astronaut faces.
        
        Returns:
        img_entry:dict = Dictionary object consisting of (a:i) pairs where a is the found astronaut, i is the index of the face attributed to the astronaut. Indicies are generated by the face_recognition library.
        """
        img_entry = {}
        unknown_encodings = None
        found_in_cache = False
        img_name = getFileName(img_path)
        if cache_img:
            if img_name in self.img_cache:
                unknown_encodings = self.img_cache[img_name]
                found_in_cache = True
        if not found_in_cache:
            try:
                unknown_image = face_recognition.load_image_file(img_path)
                unknown_encodings = face_recognition.face_encodings(unknown_image)
                self.img_cache[img_name] = unknown_encodings
            except IndexError:
                lock.acquire()
                err_log.append("\tI wasn't able to locate any faces in image: {} ... Image will not be included in results".format(img_path))
                lock.release()
                return None
        for filename in os.listdir(self.astro_pickle_dir):
            fullpath = self.astro_pickle_dir+filename
            astro = self.loadAstro(fullpath)
            if astro == None:
                return None 
            found_arr = astro.checkFace(unknown_encodings)
            face_dist = astro.faceDistance(unknown_encodings)
            if sum(found_arr) == 0 :
                continue
            else:
                img_entry[astro.filename] = []
                for i in range(len(found_arr)):
                    if found_arr[i] != 0:
                        img_entry[astro.filename].append((i,face_dist[i]))
        pickle_obj = (img_name, self.deleteRepeats(img_entry))
        makePickle("./Temp/",img_name,pickle_obj)
        sem.release()
    
    def deleteRepeats(self,faces:dict):
        unrepeated_faces = {}
        seen_index = []
        for k_1 in faces:
            for t_1 in faces[k_1]:
                current_index = t_1[0]
                current_distance = t_1[1]
                if current_index in seen_index: continue 
                seen_index.append(current_index)
                entry = (k_1,current_index)
                for k_2 in faces:
                    for t_2 in faces[k_2]:
                        if current_index == t_2[0]:
                            if t_2[1]< current_distance: 
                                entry = (k_2,current_index)
            if entry[0] in unrepeated_faces:
                if not entry[1] in unrepeated_faces[entry[0]]:
                    unrepeated_faces[entry[0]].append(entry[1])
            else:
                unrepeated_faces[entry[0]] = [entry[1]]
        return unrepeated_faces
                                    
    def findFacesDir(self, img_dir, cache_search = True):
        """Method searches all images in given directory for astronaut faces
        
        Parameters:
        img_dir:str = path to directory containing images to search
        cache_search:bool = True value indicates that dictionary should be pickled and stored for future quick retrevial. Only set to false if very confident that no images in the directory will be searched again.
        
        Side-Effect: Adds entries (img: dict) to found_faces dictionary, where img is the filepath of an image and the dict is the dictionary returned from findFaces(img)

        Returns: 
        found_faces = dictionary containing entries (img:dict) as defined in the Side-Effects. Note that the returned variable is also an instance variable of the class.
        """
        semaphore = mp.Semaphore(max(1,self.num_threads-1))
        processes = []
        lock = mp.Lock()
        print("Looking for learned faces in all images in {0} using {1} threads".format(img_dir, self.num_threads))
        for filename in os.listdir(img_dir):
            regex = re.compile(r"\.")
            if regex.split(filename)[-1] != "jpg": continue
            print("Analyzing image",filename)
            fullpath = img_dir+filename
            semaphore.acquire()
            p = Process(target = self.findFaces, args = (fullpath, semaphore,lock))
            processes.append(p)
            p.start()
        for proc in processes: proc.join()
        self.unpickleResults()
        printErr("While processing the images the following errors occured:")
        if not os.path.isdir("./img_cache") : os.mkdir("./img_cache")
        with open("./img_cache/img_cache.dat","wb") as f:
            pickle.dump(self.img_cache,f)

        return self.found_faces
            
    def itemizeKnown(self):
        #helper method, nothing to see here...
        known_astro = {}
        for filename in os.listdir(self.astro_pickle_dir):
            with open('{0}{1}'.format(self.astro_pickle_dir,filename),'rb') as f:
                known_astro.update(pickle.load(f))
        return known_astro

    def unpickleResults(self):
        for filename in os.listdir("./Temp"):
            with open("./Temp/"+filename,"rb") as f:
                result = pickle.load(f)
                self.found_faces[result[0]] = result[1]
        shutil.rmtree('./Temp')
            

        
