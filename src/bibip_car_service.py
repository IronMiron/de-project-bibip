from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale, \
    BaseModel
from typing import Dict
import json
import os


class CarService:
    MAX_LINE_LEN = 500

    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.LF_LEN = 2 if os.name == 'nt' else 1
        self.cars_fname = self.root_directory_path + '/cars.txt'
        self.cars_index_fname = (self.root_directory_path +
                                 '/cars_index.txt')
        self.models_fname = (self.root_directory_path +
                             '/models.txt')
        self.models_index_fname = (self.root_directory_path +
                                   '/models_index.txt')
        self.sales_fname = (self.root_directory_path +
                            '/sales.txt')
        self.sales_index_fname = (self.root_directory_path +
                                  '/sales_index.txt')

    def get_index(self, index_fname: str) -> Dict:
        try:
            with open(index_fname, 'r', encoding='utf-8') as f:
                index = dict()
                for iline in f:
                    val = json.loads(iline.rstrip())
                    dict.update(index, val)
        except Exception:
            index = dict()
        return index

    def get_line(self, fname: str, line_num: int) -> Dict:
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                f.seek(line_num * (self.MAX_LINE_LEN + self.LF_LEN))
                line = f.read(self.MAX_LINE_LEN).rstrip()
                line = json.loads(line)
        except Exception:
            line = dict()
        return line

    def add_to_index(self, index_fname: str, key) -> None:
        index = self.get_index(index_fname)
        line_num = len(index) + 1
        with open(index_fname, 'a', encoding='utf-8') as f:
            new_line = {
                str(key): line_num
            }
            new_line = json.dumps(new_line) + '\n'
            f.write(new_line)

    def add_to_table(self, fname: str, obj: BaseModel) -> None:
        with open(fname, 'a', encoding='utf-8') as f:
            f.write(obj.model_dump_json().ljust(self.MAX_LINE_LEN) + '\n')

    def update_table(self, fname: str, line_num: int, obj: BaseModel) -> None:
        with open(fname, 'r+', encoding='utf-8') as f:
            f.seek(line_num * (self.MAX_LINE_LEN + self.LF_LEN))
            f.write(obj.model_dump_json().ljust(self.MAX_LINE_LEN) + '\n')

    def update_key(
            self,
            fname: str,
            index_fname: str,
            old_key,
            new_key,
            new_obj: BaseModel
    ) -> None:
        index = self.get_index(index_fname)
        line_num: int = index[str(old_key)] - 1
        with open(fname, 'r+', encoding='utf-8') as f:
            f.seek(line_num * (self.MAX_LINE_LEN + self.LF_LEN))
            f.write(new_obj.model_dump_json().ljust(self.MAX_LINE_LEN) + '\n')
        dict.update(index, {str(new_key): line_num + 1})
        del index[str(old_key)]
        with open(index_fname, 'w', encoding='utf-8') as f:
            for k, v in index.items():
                f.write(json.dumps({k: v}) + '\n')

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        self.add_to_table(self.models_fname, model)
        self.add_to_index(self.models_index_fname, model.index())
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        self.add_to_table(self.cars_fname, car)
        self.add_to_index(self.cars_index_fname, car.index())
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        self.add_to_table(self.sales_fname, sale)
        self.add_to_index(self.sales_index_fname, sale.sales_number)
        cars_index = self.get_index(self.cars_index_fname)
        car_index: int = cars_index[sale.car_vin] - 1
        car = self.get_line(self.cars_fname, car_index)
        car['status'] = CarStatus.sold
        car = Car(**car)
        self.update_table(self.cars_fname, car_index, car)
        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        try:
            with open(self.cars_fname, 'r', encoding='utf-8') as f:
                roster = list()
                for iline in f:
                    car = json.loads(iline.rstrip())
                    car = Car(**car)
                    if car.status == CarStatus.available:
                        list.append(roster, car)
        except Exception:
            roster = list()
        return roster

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        res = dict()
        cars_index = self.get_index(self.cars_index_fname)
        if vin not in cars_index:
            return None
        car_index: int = cars_index[vin] - 1
        car = self.get_line(self.cars_fname, car_index)
        dict.update(res, car)
        models_index = self.get_index(self.models_index_fname)
        model_index: int = models_index[str(car['model'])] - 1
        model = self.get_line(self.models_fname, model_index)
        res['car_model_name'] = model['name']
        res['car_model_brand'] = model['brand']
        if car['status'] != CarStatus.sold:
            res['sales_date'] = None
            res['sales_cost'] = None
        else:
            with open(self.sales_fname, 'r', encoding='utf-8') as f:
                for iline in f:
                    sale = Sale(**json.loads(iline.rstrip()))
                    if sale.car_vin == car['vin']:
                        res['sales_date'] = sale.sales_date
                        res['sales_cost'] = sale.cost
                        break
        return CarFullInfo(**res)

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        cars_index = self.get_index(self.cars_index_fname)
        car_index = cars_index[vin] - 1
        car = self.get_line(self.cars_fname, car_index)
        car = Car(**car)
        car.vin = new_vin
        self.update_key(
            fname=self.cars_fname,
            index_fname=self.cars_index_fname,
            old_key=vin,
            new_key=new_vin,
            new_obj=car
        )
        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        tmp_file = self.root_directory_path + '/tmp_sales.txt'
        with (
            open(tmp_file, 'w', encoding='utf-8') as tf,
            open(self.sales_fname, 'r', encoding='utf-8') as f,
            open(self.sales_index_fname, 'w', encoding='utf-8') as i
        ):
            cntr = 1
            for iline in f:
                sale = Sale(**json.loads(iline.rstrip()))
                if sale.sales_number != sales_number:
                    tf.write(iline)
                    i.write(json.dumps({
                        sale.sales_number: cntr
                    }) + '\n')
                    cntr += 1
                else:
                    car_vin = sale.car_vin
        os.remove(self.sales_fname)
        os.rename(tmp_file, self.sales_fname)
        cars_index = self.get_index(self.cars_index_fname)
        car_index: int = cars_index[car_vin] - 1
        car = self.get_line(self.cars_fname, car_index)
        car['status'] = CarStatus.available
        car = Car(**car)
        self.update_table(self.cars_fname, car_index, car)
        return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        cars_index = self.get_index(self.cars_index_fname)
        top = dict()
        with open(self.sales_fname, 'r', encoding='utf-8') as f:
            for sline in f:
                car: dict = json.loads(sline.rstrip())
                car_index: int = cars_index[car['car_vin']] - 1
                car = self.get_line(self.cars_fname, car_index)
                if car['model'] in top:
                    top[car['model']] += 1
                else:
                    top[car['model']] = 1
        top3 = sorted(top.items(), key=lambda item: item[1], reverse=True)[:3]
        res = list()
        for line in top3:
            models_index = self.get_index(self.models_index_fname)
            model_index = models_index[str(line[0])] - 1
            model = Model(**self.get_line(self.models_fname, model_index))
            modelSaleStats = ModelSaleStats(
                car_model_name=model.name,
                brand=model.brand,
                sales_number=int(line[1])
            )
            res.append(modelSaleStats)
        print(res)
        return res
