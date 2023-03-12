import cv2
import os
import time
import numpy as np


# morphologyEx(img, operator, kernel): returns resulting image depending upon the operator specified
# - MORPH_OPEN: for open operation
# - MORPH_CLOSE: for close operation
# - MORPH_TOPHAT: for top hat operation
# - MORPH_BLACKHAT: for black hat operation
# - MORPH_GRADIENT: for morphological gradient#opening operation

class Vcap:

    _TIME_FORMAT = "%Y-%m-%d %I:%M:%S %p"
    
    def __init__(self, path: str='videos'):
        self.video_dir = path
        if not os.path.exists(self.video_dir):
            print(f"dir {self.video_dir} doesn't exist - creating..")
            os.makedirs(self.video_dir)
        if not os.path.exists(f"{self.video_dir}/frames/"):
            print(f"dir {self.video_dir}/frames/ doesn't exist - creating..")
            os.makedirs(f"{self.video_dir}/frames/")
        if not os.path.exists(f"{self.video_dir}/screenshot/"):
            print(f"dir {self.video_dir}/screenshot/ doesn't exist - creating..")
            os.makedirs(f"{self.video_dir}/screenshot/")


    #
    #
    #
    def init_backSub(self):
        self.algo = 'KNN' # KNN | MOG2
        if self.algo == 'MOG2':
            self.backSub = cv2.createBackgroundSubtractorMOG2()
        else:
            self.backSub = cv2.createBackgroundSubtractorKNN()
    

    #
    # init default vcap cnf to capture|play video
    # vfile => path of video file (src|dest - depends on mode)
    # mode  => mode to open videocap in:
    #       => cap  - open camera at index 0 (1st available)
    #       => play - open video file
    #
    def init_cap(self, mode: str) -> int:
        if mode == "cap":
            self.cap = cv2.VideoCapture(0)
        elif mode == "play":
            self.cap = cv2.VideoCapture(f'{self.video_dir}/out.mp4')
        else:
            print("invalid mode.")
            return 1

        return 0


    #
    #
    #
    def init_writer(self):
        self.frame_cnf = {
            "name": f'{self.video_dir}/out.mp4',
            "fourcc": cv2.VideoWriter_fourcc(*'mp4v'),
            "fps": 20.0,
            "frame_size": {
                "w": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "h": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            },
        }
        self.vwriter = cv2.VideoWriter(
            self.frame_cnf["name"],
            self.frame_cnf["fourcc"],
            self.frame_cnf["fps"],
            (self.frame_cnf["frame_size"]["w"], self.frame_cnf["frame_size"]["h"])
        )


    #
    # caps video to provided path
    # dstpath => dest path of video file
    #
    # obj detection using Haar Cascade Classifier:
    # - Eyes
    # - Frontal Face
    # - Full Body
    # - Upper Body
    # - Lower Body
    # - Cats
    # - Stop Signs
    # - License Plates, etc.
    #
    # rectangle params:, img/frame, start point (x/y), ending point (x/y), color (BGR), thickness (px)
    #
    def cap_video(self) -> int:

        self.init_cap("cap")
        self.init_writer()
        self.init_backSub()

        if (self.cap.isOpened() == False): 
            print(f"Error opening video file: cap open = {self.cap.isOpened()}")
            return 1

        # load xmls for eyes & face detection
        cascade_classifier_eyes = cv2.CascadeClassifier(f"{cv2.data.haarcascades}haarcascade_eye.xml")
        cascade_classifier_face = cv2.CascadeClassifier(f"{cv2.data.haarcascades}haarcascade_frontalface_alt.xml")

        lower_white = np.array([220, 220, 220], dtype=np.uint8)
        upper_white = np.array([255, 255, 255], dtype=np.uint8)

        # resize window
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # white bg
        bg_color = 255
        framecnt = 0
        while 1:

            ret, frame = self.cap.read()

            if not ret:
                break

            print(framecnt, end=" ", flush=True)

            # add text to frame
            t = time.strftime(self._TIME_FORMAT, time.localtime())
            frametxt = f"{t} :: {str(framecnt)}"
            cv2.putText(frame, frametxt, (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255))

            image_grey = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

            # change background in frame (fg_mask)
            inverted = self.invert_bg(frame, lower_white, upper_white, bg_color)

            # detect eyes|faces in frame
            self.detect_obj(frame, image_grey, cascade_classifier_eyes, (0, 255, 0), (30, 30))
            self.detect_obj(frame, image_grey, cascade_classifier_face, (0, 0, 255), (50, 50))

            if inverted.any():
                # display morphed frame
                cv2.imshow('FGMaskMorph', inverted)
                cv2.imwrite(f'{self.video_dir}/frames/' + str(framecnt) + '.png', inverted)


            # display original frame
            cv2.imshow('TestFrame', frame)

            # write frame to dest .mp4
            self.vwriter.write(frame)

            framecnt += 1

            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        self.vwriter.release()
        cv2.destroyAllWindows()
        return 0



    #
    #
    #
    def cap_img(self) -> int:
        t = time.strftime(self._TIME_FORMAT, time.localtime())
        screenshot_name = f"sc_{t}.png"
        framecnt = 0
        self.init_cap("cap")
        self.init_writer()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while 1:
            ret, frame = self.cap.read()
            if not ret:
                return 1
            # save 5th frame & exit
            if framecnt == 5:
                cv2.imwrite(f'{self.video_dir}/screenshot/' + screenshot_name, frame)
                break
            framecnt += 1

        return 0



    #
    #
    #
    def build_video_from_imgs(self):
        video_name = f'{self.video_dir}/crafted.avi'

        images = [img for img in os.listdir(f'{self.video_dir}/frames/')
                    if img.endswith(".jpg") or
                        img.endswith(".jpeg") or
                        img.endswith(".png")]
            
        frame = cv2.imread(f'{self.video_dir}/frames/{images[0]}')
        height, width, layers = frame.shape

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(video_name, fourcc, 5, (width,height))

        # frames need to be sorted!!! CURRENTLY ARE NOT

        for image in images:

            print(f"DEBUG: {image}")

            frame = cv2.imread(f'{self.video_dir}/frames/{image}')
            video.write(frame)

        cv2.destroyAllWindows()
        video.release()


    #
    # detects objects in frame
    #
    def detect_obj(
        self,
        frame: np.array,
        img_grey: np.array,
        cascade_classifier: cv2.CascadeClassifier,
        rgb_color: tuple,
        min_size: tuple
    ) -> None:

        detected = cascade_classifier.detectMultiScale(img_grey, minSize=min_size)

        if len(detected) != 0:
            for (x, y, width, height) in detected:
                cv2.rectangle(frame, (x, y), (x + height, y + width), rgb_color, 2)

        return


    #
    # creates foreground mask from frame and inverts color in it
    # ! all frame images must be in same size
    # frame => frame to invert color in (numpy array => matrix)
    # lw => lower white (numpy array of u8 vals) 
    # uw => upper white (numpy array of u8 vals)
    # bg_color => u8 int of color representation (white-black)
    # returns tuple of (fgmask, inverted frame) | empty tuple on err
    #
    def invert_bg(self, frame: np.array, lw: np.array, uw: np.array, bg_color: int) -> np.array:
        
        fg_mask = self.backSub.apply(frame)
        elipse_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

        if not frame.any() or not lw.any() or not uw.any() or bg_color > 255:
            print("invalid params for invert bg fnc.")
            return []

        try:
            # inRange uses original frame, NOT fg_mask - could also use threshold
            mask = cv2.inRange(frame, lw, uw)

            # "erase" the small white points in the resulting mask
            # Elliptical Kernel:
            #   >>> cv.getStructuringElement(cv.MORPH_ELLIPSE,(3, 3))
            #   array([[0, 0, 1, 0, 0],
            #          [1, 1, 1, 1, 1],
            #          [1, 1, 1, 1, 1],
            #          [1, 1, 1, 1, 1],
            #          [0, 0, 1, 0, 0]], dtype=uint8)

            # mask = cv.erode(mask, elipse_kernel, iterations = 1)
            # mask = cv.dilate(mask, elipse_kernel, iterations = 1)

            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, elipse_kernel)
            # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, elipse_kernel)
            # invert mask
            mask = cv2.bitwise_not(mask)

            # load background (could be an image too) - white bg
            bg = np.full(fg_mask.shape, bg_color, dtype=np.uint8)

            # get masked foreground
            fg_masked = cv2.bitwise_and(fg_mask, fg_mask, mask=mask)

            # get masked background, mask must be inverted 
            mask = cv2.bitwise_not(mask)
            bg_masked = cv2.bitwise_and(bg, bg, mask=mask)
            
            # combine masked foreground and masked background 
            final = cv2.bitwise_or(fg_masked, bg_masked)
            mask = cv2.bitwise_not(mask)  # revert mask to original
        except cv2.error as e:
            print(f"error inverting image background: {e.args[::-1]}")
            return []
        except Exception as e:
            print(f"unexpected error inverting image background: {e.args[::-1]}")
            return []
        return final

    #
    # uses fg_mask when playing video
    # srcpath => src path of video file
    #
    def play_video(self) -> int:
        if not self.video_dir:
            print("empty path.")
            return 1

        self.init_cap("play")
        self.init_backSub()
        
        if (self.cap.isOpened() == False):
            print("Error opening video file")
            return 1
        
        while(self.cap.isOpened()):

            ret, frame = self.cap.read()

            if not ret:
                break
            
            fg_mask = self.backSub.apply(frame)

            cv2.imshow('Frame', frame)
            cv2.imshow('FG Mask', fg_mask)

            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
            
        cv2.destroyAllWindows()
        self.cap.release()
        return 0




if __name__ == '__main__':
    cap_obj = Vcap()
    cap_obj.cap_video()

    print("Cap done -- exit.")
    exit(0)
