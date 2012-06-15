import sys
from PyQt4 import Qt, QtCore
from math import sin, cos, pi
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *



class PzPlot(Qwt.QwtPlot):

    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        
        self.setCanvasColor(Qt.Qt.darkCyan)

        grid = Qwt.QwtPlotGrid()
        grid.attach(self)
        grid.setMajPen(Qt.QPen(Qt.Qt.white, 0, Qt.Qt.DotLine))
        
        self.setAxisScale(Qwt.QwtPlot.xBottom, -3, 3)
        self.setAxisScale(Qwt.QwtPlot.yLeft, -2, 2)
        


    def setCanvasColor(self, color):
        self.setCanvasBackground(color)
        self.replot()


    def drawUnitcircle(self,color):
        radius = 1.0 
        steps = 1024 
        angleStep = 2 * pi / steps
        x=[sin(a * angleStep) * radius for a in range(0, steps)]
        y=[cos(a * angleStep) * radius for a in range(0, steps)]

        curve = Qwt.QwtPlotCurve()
        curve.attach(self)
        curve.setPen(Qt.QPen(Qt.Qt.black, 2))
        curve.setData(x, y)


    def insertZeros(self, roots):
        self.removeallCurves()
        self.__insertZero(Qt.Qt.blue, roots.real,roots.imag)

    def insertPoles(self, roots):
            self.__insertPole(Qt.Qt.black, roots.real,roots.imag)
            self.replot()

    def __insertZero(self, color, px, py):

        curve = Qwt.QwtPlotCurve()
        curve.attach(self)

        curve.setPen(Qt.QPen(Qt.Qt.white, 0, Qt.Qt.NoPen))
        curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
                                      Qt.QBrush(Qt.Qt.gray),
                                      Qt.QPen(color),
                                      Qt.QSize(10, 10)))
        curve.setData(px, py)

    def __insertPole(self, color, px, py):
        curve = Qwt.QwtPlotCurve()
        curve.attach(self)

        curve.setPen(Qt.QPen(Qt.Qt.white, 0, Qt.Qt.NoPen))
        curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.XCross,
                                      Qt.QBrush(Qt.Qt.gray),
                                      Qt.QPen(color),
                                      Qt.QSize(8, 8)))
        curve.setData(px, py)

    def removeallCurves(self):
        for curve in self.itemList():
            if isinstance(curve, Qwt.QwtPlotCurve):
                curve.detach()
        self.replot()



class CanvasPicker(Qt.QObject):
    curveChanged = QtCore.pyqtSignal(tuple)
    def __init__(self, plot):
        Qt.QObject.__init__(self, plot)
        self.__selectedCurve = None
        self.__selectedPoint = -1
        self.__plot = plot

        canvas = plot.canvas()
        canvas.installEventFilter(self)
        
        # We want the focus, but no focus rect.
        # The selected point will be highlighted instead.
        canvas.setFocusPolicy(Qt.Qt.StrongFocus)
        canvas.setCursor(Qt.Qt.PointingHandCursor)
        canvas.setFocusIndicator(Qwt.QwtPlotCanvas.ItemFocusIndicator)
        canvas.setFocus()
        
        canvas.setWhatsThis(
            'All points can be moved using the left mouse button '
            'or with these keys:\n\n'
            '- Up: Select next curve\n'
            '- Down: Select previous curve\n'
            '- Left, "-": Select next point\n'
            '- Right, "+": Select previous point\n'
            '- 7, 8, 9, 4, 6, 1, 2, 3: Move selected point'
            )

        self.__shiftCurveCursor(True)

    # __init__()

    def event(self, event):
        if event.type() == Qt.QEvent.User:
            self.__showCursor(True)
            return True
        return Qt.QObject.event(event)

    # event()
    
    def eventFilter(self, object, event):
        
        if event.type() == Qt.QEvent.FocusIn:
            self.__showCursor(True)
        if event.type() == Qt.QEvent.FocusOut:
            self.__showCursor(False)
         
        if event.type() == Qt.QEvent.Paint:
            Qt.QApplication.postEvent(
                self, Qt.QEvent(Qt.QEvent.User))
        elif event.type() == Qt.QEvent.MouseButtonPress:
            self.__select(event.pos())
            return True
        elif event.type() == Qt.QEvent.MouseMove:
            self.__move(event.pos())
            return True

        if event.type() == Qt.QEvent.KeyPress:
            delta = 5
            key = event.key()
            if key == Qt.Qt.Key_Up:
                self.__shiftCurveCursor(True)
                return True
            elif key == Qt.Qt.Key_Down:
                self.__shiftCurveCursor(False)
                return True
            elif key == Qt.Qt.Key_Right or key == Qt.Qt.Key_Plus:
                if self.__selectedCurve:
                    self.__shiftPointCursor(True)
                else:
                    self.__shiftCurveCursor(True)
                return True
            elif key == Qt.Qt.Key_Left or key == Qt.Qt.Key_Minus:
                if self.__selectedCurve:
                    self.__shiftPointCursor(False)
                else:
                    self.__shiftCurveCursor(True)
                return True

            if key == Qt.Qt.Key_1:
                self.__moveBy(-delta, delta)
            elif key == Qt.Qt.Key_2:
                self.__moveBy(0, delta)
            elif key == Qt.Qt.Key_3:
                self.__moveBy(delta, delta)
            elif key == Qt.Qt.Key_4:
                self.__moveBy(-delta, 0)
            elif key == Qt.Qt.Key_6:
                self.__moveBy(delta, 0)
            elif key == Qt.Qt.Key_7:
                self.__moveBy(-delta, -delta)
            elif key == Qt.Qt.Key_8:
                self.__moveBy(0, -delta)
            elif key == Qt.Qt.Key_9:
                self.__moveBy(delta, -delta)
        
        return Qwt.QwtPlot.eventFilter(self, object, event)


    def __select(self, pos):
        found, distance, point = None, 1e100, -1

        for curve in self.__plot.itemList():
            if isinstance(curve, Qwt.QwtPlotCurve):
                i, d = curve.closestPoint(pos)
                if d < distance:
                    found = curve
                    point = i
                    distance = d

        self.__showCursor(False)
        self.__selectedCurve = None
        self.__selectedPoint = -1

        if found and distance < 10:
            self.__selectedCurve = found
            self.__selectedPoint = point
            self.__showCursor(True)
            print self.__selectedCurve.data().x(point)


    def __moveBy(self, dx, dy):
        if dx == 0 and dy == 0:
            return

        curve = self.__selectedCurve
        if not curve:
            return

        x = self.__plot.transform(
            curve.xAxis(), curve.x(self.__selectedPoint)) + dx
        y = self.__plot.transform(
            curve.yAxis(), curve.y(self.__selectedPoint)) + dy
        self.__move(Qt.QPoint(x, y))


    def __move(self, pos):
        curve = self.__selectedCurve
        if not curve:
            return

        xData = zeros(curve.dataSize(), Float)
        yData = zeros(curve.dataSize(), Float)

        for i in range(curve.dataSize()):
            if i == self.__selectedPoint:
                xData[i] = self.__plot.invTransform(curve.xAxis(), pos.x())
                yData[i] = self.__plot.invTransform(curve.yAxis(), pos.y())
            else:
                xData[i] = curve.x(i)
                yData[i] = curve.y(i)
        curve.setData(xData, yData)
        self.__plot.replot()
        px=[]
        py=[]
        for c in self.__plot.itemList():
            if isinstance(c, Qwt.QwtPlotCurve):
                px.append([c.x(i) for i in range(c.dataSize())])
                py.append([c.y(i) for i in range(c.dataSize())])
        tp=(vectorize(complex)(px[0],py[0]),vectorize(complex)(px[1],py[1]))
        self.curveChanged.emit(tp)
        self.__showCursor(True)


    def __showCursor(self, showIt):
        curve = self.__selectedCurve
        if not curve:
            return

        # Use copy constructors to defeat the reference semantics.
        symbol = Qwt.QwtSymbol(curve.symbol())
        newSymbol = Qwt.QwtSymbol(symbol)
        if showIt:
            newSymbol.setBrush(symbol.brush().color().dark(150))

        doReplot = self.__plot.autoReplot()

        self.__plot.setAutoReplot(False)
        curve.setSymbol(newSymbol)

        curve.draw(self.__selectedPoint, self.__selectedPoint)

        curve.setSymbol(symbol)
        self.__plot.setAutoReplot(doReplot)
    
    def __shiftCurveCursor(self, up):
        curves = [curve for curve in self.__plot.itemList()
                  if isinstance(curve, Qwt.QwtPlotCurve)]

        if not curves:
            return

        if self.__selectedCurve in curves:
            index = curves.index(self.__selectedCurve)
            if up:
                index += 1
            else:
                index -= 1
            # keep index within [0, len(curves))
            index += len(curves)
            index %= len(curves)
        else:
            index = 0

        self.__showCursor(False)
        self.__selectedPoint = 0
        self.__selectedCurve = curves[index]
        self.__showCursor(True)


    def __shiftPointCursor(self, up):
        curve = self.__selectedCurve
        if not curve:
            return

        if up:
            index = self.__selectedPoint + 1
        else:
            index = self.__selectedPoint - 1
        # keep index within [0, curve.dataSize())
        index += curve.dataSize()
        index %= curve.dataSize()
        if index != self.__selectedPoint:
            self.__showCursor(False)
            self.__selectedPoint = index
            self.__showCursor(True)
