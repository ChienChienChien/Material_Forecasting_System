import pandas as pd
import datetime
from collections import UserDict
from config import GlobalVar
from dglib.db.dbutils import DB


class PCINode:

    def __init__(self):
        self.next_node = None
        self.prev_node = None
        self.ini_inv = None
        self.ini_inv_sub = None
        self.procurement = None
        self.consume = None
        self.consume_mff = None
        self.date = None
        self.est_inv = None
        self.est_inv_sub = None

    def set_initial_inv(self):

        self.ini_inv = self.prev_node.est_inv
        self.ini_inv_sub = self.prev_node.est_inv_sub

    def cal_est_inv(self):

        self.est_inv = self.ini_inv + self.procurement - self.consume
        # 可用庫存不考慮進貨
        self.est_inv_sub = self.ini_inv_sub - self.consume

    def __repr__(self):

        return f"[{self.date},{self.ini_inv},{self.procurement},{self.consume},{self.est_inv}]"

class PCIChain:
    
    def __init__(self, Param, material, procurement_chain, consume_chain, consume_mff_chain, inventory_chain, inventory_sub_chain):
        self.head = None
        self.Param = Param
        self.inventory_chain = inventory_chain
        self.inventory_sub_chain = inventory_sub_chain
        self.material = material
        self.procurement_chain = procurement_chain
        self.consume_chain = consume_chain
        self.consume_mff_chain = consume_mff_chain
        self.create_nodes()
        self.propagate()

    def is_empty(self):
        return self.head is None

    def append(self, new_node):
        if self.is_empty():
            self.head = new_node
        else:
            current_node = self.head
            while current_node.next_node:
                current_node = current_node.next_node
            new_node.prev_node = current_node
            current_node.next_node = new_node

    def find_node(self, date):
        node = self.head
        while node:
            if node.date == date:
                return node
            else:
                node = node.next_node

        return node

    def create_nodes(self):
        for date in self.Param.date_list:
            new_node = PCINode()
            new_node.date = date
            new_node.consume = self.consume_chain.get(date)
            new_node.consume_mff = self.consume_mff_chain.get(date)
            new_node.procurement = self.procurement_chain.get(date)
            if date < self.Param.today:
                new_node.est_inv = self.inventory_chain.get(date)
                new_node.est_inv_sub = self.inventory_sub_chain.get(date)
            self.append(new_node)

    def display_forward(self):
        node = self.head
        while node:
            print(f"{node.prev_node if node.prev_node else None} <- {node} -> {node.next_node if node.next_node else None}")
            node = node.next_node
        print("None")

    def propagate(self):
        node = self.head
        while node:
            # print(f'{self.material}|{node.date}|{node.ini_inv}|{node.procurement}|{node.consume}|{node.est_inv}')
            if node.prev_node is not None:
                node.set_initial_inv()
            if node.date >= self.Param.today:
                node.cal_est_inv()
            node = node.next_node

    def display_result(self):
        print("總庫存")
        for node in self:
            print(f'{node.date}|{node.ini_inv}|{node.procurement:.2f}|{node.consume:.2f}|{node.est_inv:.2f}')

        print("可動用庫存")
        for node in self:
            print(f'{node.date}|{node.ini_inv_sub}|{node.procurement:.2f}|{node.consume:.2f}|{node.est_inv_sub}')
        
        print("中頻爐耗用")
        for node in self:
            print(f'{node.date}|{node.consume:.2f}|{node.consume_mff:.2f}')


    def __iter__(self):

        self.current_node = self.head
        return self

    def __next__(self):

        node = self.current_node
        if node is not None:
            self.current_node = self.current_node.next_node
            return node
        else:
            raise StopIteration


class PCI(UserDict):

    def __init__(self, Param, ProcurementData, ConsumeData, InventoryData):
        self.data = {}
        self.Param = Param
        self.Procurement = ProcurementData
        self.Consume = ConsumeData
        self.Inventory = InventoryData
        self.create_chain()

    def create_chain(self):
        date_chain = self.Param.date_list
        for material in self.Param.material_list:
            procurement_chain = self.Procurement.procurement.get(material)
            consume_chain = self.Consume.consume.get(material)
            consume_mff_chain = self.Consume.consume_mff.get(material)
            inventory_chain = self.Inventory.inventory.get(material)
            inventory_sub_chain = self.Inventory.inventory_sub.get(material)
            self.data[material] = PCIChain(
                                        self.Param, material, 
                                        procurement_chain, 
                                        consume_chain, 
                                        consume_mff_chain,
                                        inventory_chain, 
                                        inventory_sub_chain
                                    )

    def to_db(self):
        data_date = self.Param.today
        sqlstr = f'''
        delete from PCI
        where DataDate = '{data_date}'
        '''
        DB.execute(sqlstr, GlobalVar.QUANTDATA_CONNSTR)

        list_of_params = []
        for material, chain in self.items():
            for node in chain:
                est_date = node.date
                if est_date > self.Param.start_date:
                    param = {
                        'data_date': data_date,
                        'est_date': est_date,
                        'material': material,
                        'ini_inv' : node.ini_inv,
                        'ini_inv_sub' : node.ini_inv_sub,
                        'procurement' : node.procurement,
                        'consume' : node.consume,
                        'consume_mff': node.consume_mff,
                        'est_inv' : node.est_inv,
                        'est_inv_sub' : node.est_inv_sub
                    }
                    list_of_params.append(param)

        sqlstr = f''' 
        insert into PCI(DataDate,EstDate,Material,IniInv,IniInvSub,Procurement,Consume,ConsumeMff,EstInv,EstInvSub)
        values(:data_date,:est_date,:material,:ini_inv,:ini_inv_sub,:procurement,:consume,:consume_mff,:est_inv,:est_inv_sub)
        '''
        DB.execute(sqlstr, GlobalVar.QUANTDATA_CONNSTR, params=list_of_params)

    def to_db_static(self):

        sqlstr = f'''
        with source as(
            SELECT *
            FROM PCI
            where DataDate = '{self.Param.today}'
        )

        MERGE INTO PCI_Static as target
        USING source
        ON target.EstDate = source.EstDate AND target.Material = source.Material

        WHEN MATCHED THEN
        UPDATE SET
            target.IniInv = source.IniInv,
            target.IniInvSub = source.IniInvSub,
            target.Procurement = source.Procurement,
            target.Consume = source.Consume,
            target.ConsumeMff = source.ConsumeMff,
            target.EstInv = source.EstInv,
            target.EstInvSub = source.EstInvSub,
            target.MDate = source.MDate

        WHEN NOT MATCHED THEN
            INSERT (EstDate, Material, IniInv, IniInvSub, Procurement, Consume, ConsumeMff, EstInv, EstInvSub, MDate)
            VALUES (source.EstDate, source.Material, source.IniInv, source.IniInvSub, source.Procurement, source.Consume, source.ConsumeMff, source.EstInv, source.EstInvSub, source.MDate);
        '''
        DB.execute(sqlstr, GlobalVar.QUANTDATA_CONNSTR)


if __name__ == '__main__':

    from data import Param, ConsumeData, InventoryData, ProcurementData
    
    param = Param()
    c = ConsumeData(param)
    i = InventoryData(param)
    p = ProcurementData(param)

    model = PCI(param, p, c, i)
