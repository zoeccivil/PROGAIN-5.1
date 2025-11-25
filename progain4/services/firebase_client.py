"""
Firebase Client for PROGAIN 5.1
Handles all Firebase (Firestore and Storage) operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Firebase client for Firestore and Storage operations.
    Implements singleton pattern for global access.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_init_done') and self._init_done:
            return
        self._init_done = True
        
        self._db = None
        self._storage = None
        self._projects_cache: List[Dict[str, Any]] = []
        self._accounts_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._categories_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._subcategories_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._transactions_cache: Dict[str, List[Dict[str, Any]]] = []
        logger.info("FirebaseClient instance created")
    
    def initialize(self, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase with credentials.
        
        Args:
            credentials_path: Path to Firebase credentials JSON file
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Try to import firebase_admin
            import firebase_admin
            from firebase_admin import credentials, firestore, storage
            
            if not firebase_admin._apps:
                if credentials_path:
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': 'progain-app.appspot.com'
                    })
                else:
                    # Try default credentials
                    firebase_admin.initialize_app()
            
            self._db = firestore.client()
            self._storage = storage.bucket()
            self._initialized = True
            logger.info("Firebase initialized successfully")
            return True
            
        except ImportError:
            logger.warning("firebase_admin not installed. Running in demo mode.")
            self._initialized = True  # Allow demo mode
            self._setup_demo_data()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            # Still allow app to run in demo mode
            self._initialized = True
            self._setup_demo_data()
            return True
    
    def _setup_demo_data(self) -> None:
        """Set up demo data for testing without Firebase."""
        logger.info("Setting up demo data for testing")
        
        # Demo projects
        self._projects_cache = [
            {"id": "proj_1", "nombre": "Proyecto Principal", "descripcion": "Proyecto de prueba"},
            {"id": "proj_2", "nombre": "Proyecto Secundario", "descripcion": "Otro proyecto"},
            {"id": "proj_3", "nombre": "Proyecto Empresarial", "descripcion": "Proyecto de la empresa"},
        ]
        
        # Demo accounts per project
        self._accounts_cache = {
            "proj_1": [
                {"id": "acc_1", "nombre": "Cuenta Corriente", "tipo": "Banco", "saldo": 15000.00},
                {"id": "acc_2", "nombre": "Caja Chica", "tipo": "Efectivo", "saldo": 2500.00},
                {"id": "acc_3", "nombre": "Tarjeta Crédito", "tipo": "Crédito", "saldo": -3500.00},
            ],
            "proj_2": [
                {"id": "acc_4", "nombre": "Cuenta Ahorro", "tipo": "Banco", "saldo": 8000.00},
                {"id": "acc_5", "nombre": "Efectivo Personal", "tipo": "Efectivo", "saldo": 500.00},
            ],
            "proj_3": [
                {"id": "acc_6", "nombre": "Cuenta Empresarial", "tipo": "Banco", "saldo": 50000.00},
                {"id": "acc_7", "nombre": "Caja Empresa", "tipo": "Efectivo", "saldo": 5000.00},
            ],
        }
        
        # Demo categories per project
        self._categories_cache = {
            "proj_1": [
                {"id": "cat_1", "nombre": "Ingresos", "tipo": "ingreso"},
                {"id": "cat_2", "nombre": "Gastos Operativos", "tipo": "gasto"},
                {"id": "cat_3", "nombre": "Gastos Administrativos", "tipo": "gasto"},
            ],
            "proj_2": [
                {"id": "cat_4", "nombre": "Salario", "tipo": "ingreso"},
                {"id": "cat_5", "nombre": "Gastos Personales", "tipo": "gasto"},
            ],
            "proj_3": [
                {"id": "cat_6", "nombre": "Ventas", "tipo": "ingreso"},
                {"id": "cat_7", "nombre": "Costos", "tipo": "gasto"},
            ],
        }
        
        # Demo subcategories per project
        self._subcategories_cache = {
            "proj_1": [
                {"id": "sub_1", "nombre": "Ventas", "categoria_id": "cat_1"},
                {"id": "sub_2", "nombre": "Servicios", "categoria_id": "cat_1"},
                {"id": "sub_3", "nombre": "Alquiler", "categoria_id": "cat_2"},
                {"id": "sub_4", "nombre": "Servicios Públicos", "categoria_id": "cat_2"},
                {"id": "sub_5", "nombre": "Papelería", "categoria_id": "cat_3"},
            ],
            "proj_2": [
                {"id": "sub_6", "nombre": "Sueldo Mensual", "categoria_id": "cat_4"},
                {"id": "sub_7", "nombre": "Alimentación", "categoria_id": "cat_5"},
            ],
            "proj_3": [
                {"id": "sub_8", "nombre": "Productos", "categoria_id": "cat_6"},
                {"id": "sub_9", "nombre": "Materiales", "categoria_id": "cat_7"},
            ],
        }
        
        # Demo transactions
        self._transactions_cache = {
            "proj_1": [
                {
                    "id": "tx_1", "fecha": datetime(2025, 1, 15), "descripcion": "Venta de servicios",
                    "monto": 5000.00, "tipo": "ingreso", "cuenta_id": "acc_1",
                    "categoria_id": "cat_1", "subcategoria_id": "sub_2", "nota": "Cliente ABC",
                    "adjuntos": []
                },
                {
                    "id": "tx_2", "fecha": datetime(2025, 1, 20), "descripcion": "Pago de alquiler",
                    "monto": -1500.00, "tipo": "gasto", "cuenta_id": "acc_1",
                    "categoria_id": "cat_2", "subcategoria_id": "sub_3", "nota": "Enero 2025",
                    "adjuntos": []
                },
                {
                    "id": "tx_3", "fecha": datetime(2025, 2, 1), "descripcion": "Venta productos",
                    "monto": 3500.00, "tipo": "ingreso", "cuenta_id": "acc_1",
                    "categoria_id": "cat_1", "subcategoria_id": "sub_1", "nota": "",
                    "adjuntos": []
                },
                {
                    "id": "tx_4", "fecha": datetime(2025, 2, 15), "descripcion": "Servicios públicos",
                    "monto": -350.00, "tipo": "gasto", "cuenta_id": "acc_2",
                    "categoria_id": "cat_2", "subcategoria_id": "sub_4", "nota": "Luz y agua",
                    "adjuntos": []
                },
                {
                    "id": "tx_5", "fecha": datetime(2025, 3, 10), "descripcion": "Pago cliente especial",
                    "monto": 8000.00, "tipo": "ingreso", "cuenta_id": "acc_1",
                    "categoria_id": "cat_1", "subcategoria_id": "sub_2", "nota": "Proyecto especial",
                    "adjuntos": [{"nombre": "factura_001.pdf", "url": "https://example.com/factura.pdf"}]
                },
                {
                    "id": "tx_6", "fecha": datetime(2025, 3, 20), "descripcion": "Compra papelería",
                    "monto": -250.00, "tipo": "gasto", "cuenta_id": "acc_2",
                    "categoria_id": "cat_3", "subcategoria_id": "sub_5", "nota": "",
                    "adjuntos": []
                },
                {
                    "id": "tx_7", "fecha": datetime(2024, 12, 15), "descripcion": "Venta diciembre",
                    "monto": 4500.00, "tipo": "ingreso", "cuenta_id": "acc_1",
                    "categoria_id": "cat_1", "subcategoria_id": "sub_1", "nota": "Cierre de año",
                    "adjuntos": []
                },
                {
                    "id": "tx_8", "fecha": datetime(2024, 11, 10), "descripcion": "Pago proveedores",
                    "monto": -2000.00, "tipo": "gasto", "cuenta_id": "acc_1",
                    "categoria_id": "cat_2", "subcategoria_id": "sub_3", "nota": "",
                    "adjuntos": []
                },
            ],
            "proj_2": [
                {
                    "id": "tx_10", "fecha": datetime(2025, 1, 1), "descripcion": "Sueldo enero",
                    "monto": 3000.00, "tipo": "ingreso", "cuenta_id": "acc_4",
                    "categoria_id": "cat_4", "subcategoria_id": "sub_6", "nota": "",
                    "adjuntos": []
                },
                {
                    "id": "tx_11", "fecha": datetime(2025, 1, 15), "descripcion": "Supermercado",
                    "monto": -500.00, "tipo": "gasto", "cuenta_id": "acc_5",
                    "categoria_id": "cat_5", "subcategoria_id": "sub_7", "nota": "",
                    "adjuntos": []
                },
            ],
            "proj_3": [
                {
                    "id": "tx_20", "fecha": datetime(2025, 2, 1), "descripcion": "Venta productos empresa",
                    "monto": 25000.00, "tipo": "ingreso", "cuenta_id": "acc_6",
                    "categoria_id": "cat_6", "subcategoria_id": "sub_8", "nota": "Cliente corporativo",
                    "adjuntos": []
                },
            ],
        }
    
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._initialized
    
    # ==================== PROJECTS ====================
    
    def get_proyectos(self) -> List[Dict[str, Any]]:
        """
        Get all projects.
        
        Returns:
            List of project dictionaries with 'id' and 'nombre' fields.
        """
        if not self._initialized:
            logger.warning("Firebase not initialized")
            return []
        
        if self._db:
            try:
                docs = self._db.collection('proyectos').stream()
                projects = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    projects.append(data)
                logger.info(f"Loaded {len(projects)} projects from Firestore")
                return projects
            except Exception as e:
                logger.error(f"Error loading projects: {e}")
                return self._projects_cache
        else:
            # Demo mode
            logger.debug(f"Returning {len(self._projects_cache)} demo projects")
            return self._projects_cache
    
    # ==================== ACCOUNTS ====================
    
    def get_cuentas_by_proyecto(self, proyecto_id: str) -> List[Dict[str, Any]]:
        """
        Get all accounts for a project.
        
        Args:
            proyecto_id: The project ID
            
        Returns:
            List of account dictionaries.
        """
        if not self._initialized:
            return []
        
        if self._db:
            try:
                docs = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('cuentas').stream()
                accounts = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    accounts.append(data)
                logger.info(f"Loaded {len(accounts)} accounts for project {proyecto_id}")
                return accounts
            except Exception as e:
                logger.error(f"Error loading accounts: {e}")
                return self._accounts_cache.get(proyecto_id, [])
        else:
            return self._accounts_cache.get(proyecto_id, [])
    
    # ==================== CATEGORIES ====================
    
    def get_categorias_by_proyecto(self, proyecto_id: str) -> List[Dict[str, Any]]:
        """Get all categories for a project."""
        if not self._initialized:
            return []
        
        if self._db:
            try:
                docs = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('categorias').stream()
                categories = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    categories.append(data)
                return categories
            except Exception as e:
                logger.error(f"Error loading categories: {e}")
                return self._categories_cache.get(proyecto_id, [])
        else:
            return self._categories_cache.get(proyecto_id, [])
    
    def get_subcategorias_by_proyecto(self, proyecto_id: str) -> List[Dict[str, Any]]:
        """Get all subcategories for a project."""
        if not self._initialized:
            return []
        
        if self._db:
            try:
                docs = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('subcategorias').stream()
                subcategories = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    subcategories.append(data)
                return subcategories
            except Exception as e:
                logger.error(f"Error loading subcategories: {e}")
                return self._subcategories_cache.get(proyecto_id, [])
        else:
            return self._subcategories_cache.get(proyecto_id, [])
    
    # ==================== TRANSACTIONS ====================
    
    def get_transacciones_by_proyecto(self, proyecto_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a project."""
        if not self._initialized:
            return []
        
        if self._db:
            try:
                docs = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('transacciones').order_by('fecha', direction='DESCENDING').stream()
                transactions = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    # Convert Firestore timestamp to datetime
                    if 'fecha' in data and hasattr(data['fecha'], 'to_datetime'):
                        data['fecha'] = data['fecha'].to_datetime()
                    transactions.append(data)
                logger.info(f"Loaded {len(transactions)} transactions for project {proyecto_id}")
                return transactions
            except Exception as e:
                logger.error(f"Error loading transactions: {e}")
                return self._transactions_cache.get(proyecto_id, [])
        else:
            return self._transactions_cache.get(proyecto_id, [])
    
    def get_transacciones_by_cuenta(self, proyecto_id: str, cuenta_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific account."""
        all_tx = self.get_transacciones_by_proyecto(proyecto_id)
        return [tx for tx in all_tx if tx.get('cuenta_id') == cuenta_id]
    
    def get_transacciones_por_proyecto_y_periodo(
        self, proyecto_id: str, fecha_inicio: datetime, fecha_fin: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a project within a date range.
        
        Args:
            proyecto_id: Project ID
            fecha_inicio: Start date (inclusive)
            fecha_fin: End date (inclusive)
            
        Returns:
            List of transactions within the date range.
        """
        all_tx = self.get_transacciones_by_proyecto(proyecto_id)
        filtered = []
        for tx in all_tx:
            fecha = tx.get('fecha')
            if fecha:
                if isinstance(fecha, str):
                    fecha = datetime.fromisoformat(fecha)
                if fecha_inicio <= fecha <= fecha_fin:
                    filtered.append(tx)
        logger.debug(f"Filtered {len(filtered)} transactions for period {fecha_inicio} to {fecha_fin}")
        return filtered
    
    def agregar_transaccion_a_proyecto(self, proyecto_id: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Add a new transaction to a project.
        
        Args:
            proyecto_id: Project ID
            data: Transaction data
            
        Returns:
            Transaction ID if successful, None otherwise.
        """
        if not self._initialized:
            return None
        
        if self._db:
            try:
                doc_ref = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('transacciones').add(data)
                tx_id = doc_ref[1].id
                logger.info(f"Added transaction {tx_id} to project {proyecto_id}")
                return tx_id
            except Exception as e:
                logger.error(f"Error adding transaction: {e}")
                return None
        else:
            # Demo mode - add to cache
            import uuid
            tx_id = f"tx_{uuid.uuid4().hex[:8]}"
            data['id'] = tx_id
            if proyecto_id not in self._transactions_cache:
                self._transactions_cache[proyecto_id] = []
            self._transactions_cache[proyecto_id].append(data)
            logger.info(f"Added demo transaction {tx_id}")
            return tx_id
    
    def actualizar_transaccion(self, proyecto_id: str, tx_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing transaction."""
        if not self._initialized:
            return False
        
        if self._db:
            try:
                self._db.collection('proyectos').document(proyecto_id)\
                    .collection('transacciones').document(tx_id).update(data)
                logger.info(f"Updated transaction {tx_id}")
                return True
            except Exception as e:
                logger.error(f"Error updating transaction: {e}")
                return False
        else:
            # Demo mode
            if proyecto_id in self._transactions_cache:
                for tx in self._transactions_cache[proyecto_id]:
                    if tx.get('id') == tx_id:
                        tx.update(data)
                        logger.info(f"Updated demo transaction {tx_id}")
                        return True
            return False
    
    def eliminar_transaccion(self, proyecto_id: str, tx_id: str) -> bool:
        """Delete a transaction."""
        if not self._initialized:
            return False
        
        if self._db:
            try:
                self._db.collection('proyectos').document(proyecto_id)\
                    .collection('transacciones').document(tx_id).delete()
                logger.info(f"Deleted transaction {tx_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting transaction: {e}")
                return False
        else:
            # Demo mode
            if proyecto_id in self._transactions_cache:
                self._transactions_cache[proyecto_id] = [
                    tx for tx in self._transactions_cache[proyecto_id] if tx.get('id') != tx_id
                ]
                logger.info(f"Deleted demo transaction {tx_id}")
                return True
            return False
    
    # ==================== TRANSFERS (Task 4) ====================
    
    def crear_transferencia(
        self, proyecto_id: str, cuenta_origen_id: str, cuenta_destino_id: str,
        monto: float, fecha: datetime, nota: str = ""
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a transfer between two accounts (two linked transactions).
        
        Args:
            proyecto_id: Project ID
            cuenta_origen_id: Source account ID
            cuenta_destino_id: Destination account ID
            monto: Transfer amount (positive)
            fecha: Transfer date
            nota: Optional note
            
        Returns:
            Tuple of (outgoing_tx_id, incoming_tx_id) or (None, None) on failure.
        """
        if not self._initialized:
            return None, None
        
        # Create outgoing transaction
        tx_salida = {
            "fecha": fecha,
            "descripcion": f"Transferencia saliente",
            "monto": -abs(monto),
            "tipo": "Transferencia Salida",
            "cuenta_id": cuenta_origen_id,
            "cuenta_destino_id": cuenta_destino_id,
            "nota": nota,
            "adjuntos": []
        }
        
        # Create incoming transaction
        tx_entrada = {
            "fecha": fecha,
            "descripcion": f"Transferencia entrante",
            "monto": abs(monto),
            "tipo": "Transferencia Entrada",
            "cuenta_id": cuenta_destino_id,
            "cuenta_origen_id": cuenta_origen_id,
            "nota": nota,
            "adjuntos": []
        }
        
        # Try to add both transactions atomically
        if self._db:
            try:
                batch = self._db.batch()
                
                ref_salida = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('transacciones').document()
                ref_entrada = self._db.collection('proyectos').document(proyecto_id)\
                    .collection('transacciones').document()
                
                # Link transactions to each other
                tx_salida['transferencia_vinculada'] = ref_entrada.id
                tx_entrada['transferencia_vinculada'] = ref_salida.id
                
                batch.set(ref_salida, tx_salida)
                batch.set(ref_entrada, tx_entrada)
                batch.commit()
                
                logger.info(f"Created transfer: {ref_salida.id} -> {ref_entrada.id}")
                return ref_salida.id, ref_entrada.id
                
            except Exception as e:
                logger.error(f"Error creating transfer: {e}")
                return None, None
        else:
            # Demo mode
            import uuid
            id_salida = f"tx_{uuid.uuid4().hex[:8]}"
            id_entrada = f"tx_{uuid.uuid4().hex[:8]}"
            
            tx_salida['id'] = id_salida
            tx_salida['transferencia_vinculada'] = id_entrada
            tx_entrada['id'] = id_entrada
            tx_entrada['transferencia_vinculada'] = id_salida
            
            if proyecto_id not in self._transactions_cache:
                self._transactions_cache[proyecto_id] = []
            
            self._transactions_cache[proyecto_id].append(tx_salida)
            self._transactions_cache[proyecto_id].append(tx_entrada)
            
            logger.info(f"Created demo transfer: {id_salida} -> {id_entrada}")
            return id_salida, id_entrada
    
    # ==================== STORAGE (Task 5) ====================
    
    def upload_file_to_storage(
        self, proyecto_id: str, year: int, month: int, 
        filename: str, file_data: bytes, content_type: str = 'application/octet-stream'
    ) -> Optional[str]:
        """
        Upload a file to Firebase Storage.
        
        Args:
            proyecto_id: Project ID
            year: Year for organizing files
            month: Month for organizing files
            filename: Original filename
            file_data: File content as bytes
            content_type: MIME type
            
        Returns:
            Download URL if successful, None otherwise.
        """
        if not self._initialized:
            return None
        
        storage_path = f"Proyecto/{proyecto_id}/{year}/{month:02d}/{filename}"
        
        if self._storage:
            try:
                blob = self._storage.blob(storage_path)
                blob.upload_from_string(file_data, content_type=content_type)
                blob.make_public()
                url = blob.public_url
                logger.info(f"Uploaded file to {storage_path}")
                return url
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                return None
        else:
            # Demo mode - return fake URL
            fake_url = f"https://storage.example.com/{storage_path}"
            logger.info(f"Demo: Would upload to {storage_path}")
            return fake_url
    
    def upload_adjuntos_transaccion(
        self, proyecto_id: str, fecha: datetime, archivos: List[Tuple[str, bytes, str]]
    ) -> List[Dict[str, str]]:
        """
        Upload multiple attachments for a transaction.
        
        Args:
            proyecto_id: Project ID
            fecha: Transaction date (for organizing files)
            archivos: List of (filename, data, content_type) tuples
            
        Returns:
            List of attachment info dicts with 'nombre' and 'url'.
        """
        adjuntos = []
        for filename, data, content_type in archivos:
            url = self.upload_file_to_storage(
                proyecto_id, fecha.year, fecha.month, filename, data, content_type
            )
            if url:
                adjuntos.append({
                    "nombre": filename,
                    "url": url,
                    "tipo": content_type
                })
        return adjuntos
    
    # ==================== CASHFLOW (Task 2) ====================
    
    def calcular_flujo_caja_por_cuenta(
        self, proyecto_id: str, fecha_inicio: datetime, fecha_fin: datetime
    ) -> List[Dict[str, Any]]:
        """
        Calculate cash flow summary by account.
        
        Returns:
            List of dicts with account info, total income, expenses, and balance.
        """
        transactions = self.get_transacciones_por_proyecto_y_periodo(
            proyecto_id, fecha_inicio, fecha_fin
        )
        accounts = self.get_cuentas_by_proyecto(proyecto_id)
        
        # Initialize per-account totals
        account_map = {acc['id']: acc['nombre'] for acc in accounts}
        totals = defaultdict(lambda: {"ingresos": 0, "gastos": 0})
        
        for tx in transactions:
            cuenta_id = tx.get('cuenta_id')
            monto = tx.get('monto', 0)
            if monto > 0:
                totals[cuenta_id]["ingresos"] += monto
            else:
                totals[cuenta_id]["gastos"] += abs(monto)
        
        result = []
        for cuenta_id, data in totals.items():
            result.append({
                "cuenta_id": cuenta_id,
                "cuenta_nombre": account_map.get(cuenta_id, "Desconocida"),
                "total_ingresos": data["ingresos"],
                "total_gastos": data["gastos"],
                "balance": data["ingresos"] - data["gastos"]
            })
        
        return result
    
    def calcular_flujo_caja_mensual(
        self, proyecto_id: str, fecha_inicio: datetime, fecha_fin: datetime
    ) -> List[Dict[str, Any]]:
        """
        Calculate cash flow summary by month.
        
        Returns:
            List of dicts with year-month, income, expenses, and balance.
        """
        transactions = self.get_transacciones_por_proyecto_y_periodo(
            proyecto_id, fecha_inicio, fecha_fin
        )
        
        monthly = defaultdict(lambda: {"ingresos": 0, "gastos": 0})
        
        for tx in transactions:
            fecha = tx.get('fecha')
            if fecha:
                if isinstance(fecha, str):
                    fecha = datetime.fromisoformat(fecha)
                key = f"{fecha.year}-{fecha.month:02d}"
                monto = tx.get('monto', 0)
                if monto > 0:
                    monthly[key]["ingresos"] += monto
                else:
                    monthly[key]["gastos"] += abs(monto)
        
        result = []
        for key in sorted(monthly.keys()):
            data = monthly[key]
            result.append({
                "periodo": key,
                "ingresos": data["ingresos"],
                "gastos": data["gastos"],
                "balance": data["ingresos"] - data["gastos"]
            })
        
        return result


# Singleton instance
firebase_client = FirebaseClient()
