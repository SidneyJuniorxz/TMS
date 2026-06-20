from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.delivery import Delivery
from ..models.city import City
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
import csv
import io

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


# --- Pydantic Schemas ---

class DeliveryCreate(BaseModel):
    origem_cidade: str
    origem_cep: str
    destino_cidade: str
    destino_cep: str
    peso_kg: float
    comprimento_cm: float
    largura_cm: float
    altura_cm: float
    deadline_days: int = 5
    descricao: Optional[str] = ""
    prioridade: Optional[str] = "media"
    observacao: Optional[str] = ""

    @field_validator("origem_cep", "destino_cep")
    @classmethod
    def cep_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("CEP é obrigatório e não pode estar vazio")
        return v.strip()

    @field_validator("origem_cidade", "destino_cidade")
    @classmethod
    def cidade_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Cidade é obrigatória e não pode estar vazia")
        return v.strip()

    @field_validator("peso_kg")
    @classmethod
    def peso_must_be_positive(cls, v):
        if v is None or v <= 0:
            raise ValueError("Peso deve ser maior que zero")
        return v

    @field_validator("comprimento_cm", "largura_cm", "altura_cm")
    @classmethod
    def dimensions_must_be_positive(cls, v):
        if v is None or v <= 0:
            raise ValueError("Dimensões (comprimento, largura, altura) devem ser maiores que zero")
        return v


class DeliveryResponse(BaseModel):
    id: int
    origem_cidade: str
    origem_cep: str
    destino_cidade: str
    destino_cep: str
    peso_kg: float
    comprimento_cm: float
    largura_cm: float
    altura_cm: float
    volume_m3: float
    deadline_days: int
    descricao: Optional[str] = ""
    prioridade: Optional[str] = "media"
    observacao: Optional[str] = ""

    # Legacy fields for backward-compatible display
    city_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


def calculate_volume_m3(comprimento_cm: float, largura_cm: float, altura_cm: float) -> float:
    """Calcula cubagem: volume_m3 = comp * larg * alt / 1_000_000"""
    return round(comprimento_cm * largura_cm * altura_cm / 1_000_000, 6)


# --- Endpoints ---

@router.get("/", response_model=list[DeliveryResponse])
def list_deliveries(db: Session = Depends(get_db)):
    return db.query(Delivery).all()


@router.post("/", response_model=DeliveryResponse)
def create_delivery(delivery: DeliveryCreate, db: Session = Depends(get_db)):
    volume = calculate_volume_m3(delivery.comprimento_cm, delivery.largura_cm, delivery.altura_cm)

    # Try to resolve city_id from destino_cidade for map plotting
    city = db.query(City).filter(City.name.ilike(delivery.destino_cidade)).first()

    db_delivery = Delivery(
        origem_cidade=delivery.origem_cidade,
        origem_cep=delivery.origem_cep,
        destino_cidade=delivery.destino_cidade,
        destino_cep=delivery.destino_cep,
        peso_kg=delivery.peso_kg,
        comprimento_cm=delivery.comprimento_cm,
        largura_cm=delivery.largura_cm,
        altura_cm=delivery.altura_cm,
        volume_m3=volume,
        deadline_days=delivery.deadline_days,
        descricao=delivery.descricao or "",
        prioridade=delivery.prioridade or "media",
        observacao=delivery.observacao or "",
        city_id=city.id if city else None,
        # Legacy fields
        weight=delivery.peso_kg,
        volume=volume,
    )
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery


@router.delete("/{delivery_id}")
def delete_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega não encontrada")
    db.delete(delivery)
    db.commit()
    return {"message": f"Entrega #{delivery_id} removida com sucesso"}


@router.delete("/")
def delete_all_deliveries(db: Session = Depends(get_db)):
    count = db.query(Delivery).delete()
    db.commit()
    return {"message": f"{count} entregas removidas com sucesso"}


@router.post("/upload-csv")
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Apenas arquivos CSV são permitidos")

    try:
        contents = file.file.read()
        # Try UTF-8 first, then latin-1 for Brazilian CSV files
        try:
            text = contents.decode('utf-8-sig')  # Handle BOM
        except UnicodeDecodeError:
            text = contents.decode('latin-1')

        buffer = io.StringIO(text)
        reader = csv.DictReader(buffer, delimiter=',')

        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio ou sem cabeçalhos")

        # Normalize headers
        raw_headers = {h.strip().lower().replace(" ", "_"): h for h in reader.fieldnames}

        # Map expected columns (flexible matching)
        def find_header(candidates):
            for c in candidates:
                for raw_key, original in raw_headers.items():
                    if c in raw_key:
                        return original
            return None

        h_origem_cidade = find_header(["origem_cidade", "origin_city", "origem"])
        h_origem_cep = find_header(["origem_cep", "origin_cep", "cep_origem"])
        h_destino_cidade = find_header(["destino_cidade", "dest_city", "destino", "city"])
        h_destino_cep = find_header(["destino_cep", "dest_cep", "cep_destino", "cep"])
        h_peso = find_header(["peso_kg", "peso", "weight"])
        h_comprimento = find_header(["comprimento_cm", "comprimento", "length"])
        h_largura = find_header(["largura_cm", "largura", "width"])
        h_altura = find_header(["altura_cm", "altura", "height"])
        h_deadline = find_header(["deadline", "prazo", "deadline_days"])
        h_descricao = find_header(["descricao", "description", "desc"])
        h_prioridade = find_header(["prioridade", "priority"])
        h_observacao = find_header(["observacao", "obs", "observation", "note"])

        # Validate required headers
        missing = []
        if not h_origem_cidade:
            missing.append("origem_cidade")
        if not h_origem_cep:
            missing.append("origem_cep")
        if not h_destino_cidade:
            missing.append("destino_cidade")
        if not h_destino_cep:
            missing.append("destino_cep")
        if not h_peso:
            missing.append("peso_kg")
        if not h_comprimento:
            missing.append("comprimento_cm")
        if not h_largura:
            missing.append("largura_cm")
        if not h_altura:
            missing.append("altura_cm")

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Colunas obrigatórias ausentes no CSV: {', '.join(missing)}. "
                       f"Colunas encontradas: {', '.join(reader.fieldnames)}"
            )

        imported_count = 0
        errors = []

        for idx, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            row_errors = []

            # Required text fields
            origem_cidade = row.get(h_origem_cidade, "").strip()
            origem_cep = row.get(h_origem_cep, "").strip()
            destino_cidade = row.get(h_destino_cidade, "").strip()
            destino_cep = row.get(h_destino_cep, "").strip()

            if not origem_cidade:
                row_errors.append("origem_cidade vazia")
            if not origem_cep:
                row_errors.append("origem_cep vazio")
            if not destino_cidade:
                row_errors.append("destino_cidade vazia")
            if not destino_cep:
                row_errors.append("destino_cep vazio")

            # Numeric fields with validation
            try:
                peso = float(row.get(h_peso, "0").strip().replace(",", "."))
                if peso <= 0:
                    row_errors.append("peso_kg deve ser > 0")
            except (ValueError, AttributeError):
                row_errors.append("peso_kg inválido (não é número)")
                peso = 0

            try:
                comprimento = float(row.get(h_comprimento, "0").strip().replace(",", "."))
                if comprimento <= 0:
                    row_errors.append("comprimento_cm deve ser > 0")
            except (ValueError, AttributeError):
                row_errors.append("comprimento_cm inválido")
                comprimento = 0

            try:
                largura = float(row.get(h_largura, "0").strip().replace(",", "."))
                if largura <= 0:
                    row_errors.append("largura_cm deve ser > 0")
            except (ValueError, AttributeError):
                row_errors.append("largura_cm inválido")
                largura = 0

            try:
                altura = float(row.get(h_altura, "0").strip().replace(",", "."))
                if altura <= 0:
                    row_errors.append("altura_cm deve ser > 0")
            except (ValueError, AttributeError):
                row_errors.append("altura_cm inválido")
                altura = 0

            # Optional fields
            try:
                deadline = int(row.get(h_deadline, "5").strip()) if h_deadline else 5
            except (ValueError, AttributeError):
                deadline = 5

            descricao = row.get(h_descricao, "").strip() if h_descricao else ""
            prioridade = row.get(h_prioridade, "media").strip() if h_prioridade else "media"
            observacao = row.get(h_observacao, "").strip() if h_observacao else ""

            if row_errors:
                errors.append(f"Linha {idx}: {'; '.join(row_errors)}")
                continue

            # Calculate volume
            volume_m3 = calculate_volume_m3(comprimento, largura, altura)

            # Try to resolve city_id from destino_cidade
            city = db.query(City).filter(City.name.ilike(destino_cidade)).first()

            db_delivery = Delivery(
                origem_cidade=origem_cidade,
                origem_cep=origem_cep,
                destino_cidade=destino_cidade,
                destino_cep=destino_cep,
                peso_kg=peso,
                comprimento_cm=comprimento,
                largura_cm=largura,
                altura_cm=altura,
                volume_m3=volume_m3,
                deadline_days=deadline,
                descricao=descricao,
                prioridade=prioridade,
                observacao=observacao,
                city_id=city.id if city else None,
                weight=peso,
                volume=volume_m3,
            )
            db.add(db_delivery)
            imported_count += 1

        db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")

    return {
        "message": f"Importação concluída: {imported_count} entregas importadas com sucesso.",
        "imported": imported_count,
        "errors": errors,
        "total_errors": len(errors)
    }


@router.get("/template-csv")
def download_template_csv():
    """Retorna um arquivo CSV modelo com dados fictícios da Grande São Paulo."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "origem_cidade", "origem_cep", "destino_cidade", "destino_cep",
        "peso_kg", "comprimento_cm", "largura_cm", "altura_cm",
        "deadline", "descricao", "prioridade", "observacao"
    ])

    # Sample data — Grande São Paulo
    sample_data = [
        ["Guarulhos", "07000-000", "Osasco", "06000-000", 150, 80, 60, 50, 3, "Peças automotivas", "alta", "Frágil"],
        ["Guarulhos", "07000-000", "Santo André", "09000-000", 300, 120, 80, 60, 5, "Eletrodomésticos", "media", ""],
        ["Guarulhos", "07000-000", "São Bernardo do Campo", "09600-000", 80, 50, 40, 30, 2, "Componentes eletrônicos", "alta", "Urgente"],
        ["Guarulhos", "07000-000", "Barueri", "06400-000", 500, 150, 100, 80, 7, "Materiais de construção", "baixa", ""],
        ["Guarulhos", "07000-000", "São Paulo", "01000-000", 200, 100, 70, 50, 4, "Alimentos secos", "media", "Manter seco"],
        ["Guarulhos", "07000-000", "Mogi das Cruzes", "08700-000", 120, 90, 60, 40, 3, "Medicamentos", "alta", "Temperatura controlada"],
        ["Guarulhos", "07000-000", "Diadema", "09900-000", 450, 130, 90, 70, 6, "Bobinas de aço", "media", "Peso elevado"],
        ["Guarulhos", "07000-000", "Cotia", "06700-000", 75, 40, 35, 25, 4, "Cosméticos", "baixa", ""],
    ]

    for row in sample_data:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=modelo_importacao_entregas.csv"}
    )
