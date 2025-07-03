# import matplotlib.pyplot as plt
# import matplotlib.patches as patches
# import cv2

# def visualize_extracted_data(image_path, ocr_results, extracted_data, field_labels):
#     """
#     Visualiza las etiquetas y los valores extraídos sobre la imagen.
    
#     Parameters:
#         image_path (str): Ruta a la imagen procesada.
#         ocr_results (list): Lista de resultados de OCR con bounding boxes y texto.
#         extracted_data (dict): Diccionario con los campos extraídos.
#         field_labels (dict): Diccionario mapeando etiquetas a nombres de campos.
#     """
#     image = cv2.imread(image_path)
#     image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     fig, ax = plt.subplots(figsize=(20, 20))
#     ax.imshow(image_rgb)

#     for label, field_name in field_labels.items():
#         for item in ocr_results:
#             text = item[1][0]
#             if label.lower() in text.lower():
#                 box = item[0]
#                 x_start, y_start = box[0]
#                 x_end, y_end = box[2]
#                 rect = patches.Rectangle((x_start, y_start), x_end - x_start, y_end - y_start, linewidth=2, edgecolor='r', facecolor='none')
#                 ax.add_patch(rect)
#                 plt.text(x_start, y_start - 10, label, color='red', fontsize=12, weight='bold')
                
#                 # Encontrar el valor
#                 value = extracted_data.get(field_name, "No encontrado")
#                 plt.text(x_start + 10, y_start + 20, value, color='blue', fontsize=12, weight='bold')
#                 break

#     plt.axis('off')
#     plt.show()

# # Uso dentro de UploadLicenseView después de extraer los datos
# visualize_extracted_data(preprocessed_image_path, raw_result, data, field_labels)
