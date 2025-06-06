class Intencion:

    def __init__(self, deseo, plan):
        self.deseo = deseo
        self.plan = plan

    def __repr__(self):
        return f"Intencion(deseo={self.deseo}, plan={self.plan})"
